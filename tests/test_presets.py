import copy
import unittest
from unittest.mock import patch

from uniconv import UnitConverter


class TestPresets(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_names_unknown_and_independent_raw_mapping(self):
        self.assertEqual(self.uc.list_presets(), ["SI", "TECH", "IMPERIAL"])
        self.assertIsNone(self.uc.get_preset("unknown"))
        self.assertIsNone(self.uc.apply_preset("unknown"))

        raw = self.uc.get_preset("SI")
        self.assertEqual(raw, self.uc.presets["SI"]["units"])
        raw["0"] = "changed"
        self.assertEqual(self.uc.get_preset("SI")["0"], "МПа")

        names = self.uc.list_presets()
        names.clear()
        self.assertEqual(len(self.uc.list_presets()), 3)

    def test_all_builtin_presets_filter_invalid_pairs_and_use_registry_ui(self):
        before = copy.deepcopy(self.uc.parameters)
        expected_invalid_counts = {"SI": 2, "TECH": 1, "IMPERIAL": 10}

        for name in self.uc.list_presets():
            raw = self.uc.get_preset(name)
            expected = {
                key: code
                for key, code in raw.items()
                if key in before and code in before[key]["factors"]
            }
            with self.assertLogs("uniconv.converter", level="WARNING") as logs:
                applied = self.uc.apply_preset(name)

            self.assertEqual(set(applied), set(expected))
            self.assertEqual(len(logs.output), len(raw) - len(expected))
            self.assertEqual(len(logs.output), expected_invalid_counts[name])
            self.assertTrue(
                all(r.levelname == "WARNING" for r in logs.records))

            for type_id, value in applied.items():
                self.assertEqual(
                    value,
                    {
                        "code": expected[type_id],
                        "ui": before[type_id]["display_labels"][expected[type_id]],
                    },
                )
            self.assertEqual(self.uc.get_preset(name), raw)

        self.assertEqual(self.uc.parameters, before)

    def test_invalid_ids_and_codes_are_logged_and_valid_pairs_survive(self):
        raw_test = {"0": "кгс/см2", "999": "x", "1": "bad"}
        self.uc.presets["test"] = {"units": dict(raw_test)}

        with self.assertLogs("uniconv.converter", level="WARNING") as logs:
            applied = self.uc.apply_preset("test")

        self.assertEqual(applied, {"0": {"code": "кгс/см2", "ui": "кгс/см²"}})
        self.assertEqual(len(logs.output), 2)
        self.assertEqual([r.levelname for r in logs.records],
                         ["WARNING", "WARNING"])
        self.assertIn("999", logs.output[0])
        self.assertIn("bad", logs.output[1])

        self.assertEqual(self.uc.get_preset("test"), raw_test)
        self.assertNotIn("test", UnitConverter().list_presets())

        raw_ui_and_name = {"0": "кгс/см²", "Давление": "МПа", "1": "Re"}
        self.uc.presets["test_ui_and_name"] = {"units": dict(raw_ui_and_name)}
        with self.assertLogs("uniconv.converter", level="WARNING") as logs_ui:
            applied_ui = self.uc.apply_preset("test_ui_and_name")

        self.assertEqual(applied_ui, {"1": {"code": "Re", "ui": "°Re"}})
        self.assertEqual(len(logs_ui.output), 2)
        self.assertEqual([r.levelname for r in logs_ui.records], [
                         "WARNING", "WARNING"])
        self.assertEqual(self.uc.get_preset(
            "test_ui_and_name"), raw_ui_and_name)

        applied["0"]["ui"] = "changed"
        self.assertEqual(self.uc.get_available_units("0")[0]["ui"], "кгс/см²")

    def test_valid_empty_and_partial_presets_do_not_log(self):
        self.uc.presets["partial"] = {"units": {"0": "Па"}}
        self.uc.presets["valid_multi"] = {"units": {"0": "кгс/см2", "1": "Re"}}
        self.uc.presets["empty"] = {"units": {}}

        with patch("uniconv.converter.logger.warning") as warning:
            self.assertEqual(
                self.uc.apply_preset("partial"),
                {"0": {"code": "Па", "ui": "Па"}},
            )
            self.assertEqual(
                self.uc.apply_preset("valid_multi"),
                {
                    "0": {"code": "кгс/см2", "ui": "кгс/см²"},
                    "1": {"code": "Re", "ui": "°Re"},
                },
            )
            self.assertEqual(self.uc.apply_preset("empty"), {})
            warning.assert_not_called()

        self.assertEqual(self.uc.get_preset("valid_multi"),
                         {"0": "кгс/см2", "1": "Re"})


if __name__ == "__main__":
    unittest.main()
