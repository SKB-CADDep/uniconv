import unittest

from uniconv import UnitConverter, UnknownParameterError, UnknownUnitError


class TestApiById(unittest.TestCase):
    def setUp(self) -> None:
        self.uc = UnitConverter()

    def test_methods_on_id_0(self) -> None:
        info = self.uc.get_parameter_info("0")
        self.assertEqual(
            info,
            {
                "id": "0",
                "name_RU": "Давление",
                "name_ENG": "Pressure",
                "base_unit": "кгс/см2",
            },
        )
        self.assertEqual(self.uc.get_base_unit("0"), "кгс/см2")

        units = self.uc.get_available_units("0")
        self.assertGreater(len(units), 1)
        self.assertEqual(units[0], {"code": "кгс/см2", "ui": "кгс/см²"})

        codes = [u["code"] for u in units]
        self.assertIn("бар", codes)
        self.assertIn("МПа", codes)

        base_val = self.uc.to_base(10, "бар", "0")
        self.assertAlmostEqual(
            self.uc.convert(10, "бар", "кгс/см2", "0"),
            base_val,
            places=12,
        )
        self.assertAlmostEqual(
            self.uc.from_base(base_val, "бар", "0"),
            10.0,
            places=10,
        )
        self.assertAlmostEqual(
            self.uc.convert(10, from_u="бар", to_u="МПа", type_id="0"),
            1.0,
            places=12,
        )
        self.assertEqual(self.uc.convert(-3.5, "бар", "бар", "0"), -3.5)

    def test_methods_on_id_47(self) -> None:
        info = self.uc.get_parameter_info("47")
        self.assertEqual(info["id"], "47")
        self.assertTrue(info["name_RU"])
        self.assertTrue(info["name_ENG"])
        self.assertEqual(set(info.keys()), {"id", "name_RU", "name_ENG", "base_unit"})

        base_code = self.uc.get_base_unit("47")
        self.assertEqual(base_code, info["base_unit"])

        units = self.uc.get_available_units("47")
        self.assertGreater(len(units), 1)
        codes = [u["code"] for u in units]
        self.assertIn(base_code, codes)
        for item in units:
            self.assertEqual(set(item.keys()), {"code", "ui"})
            self.assertIsInstance(item["code"], str)
            self.assertIsInstance(item["ui"], str)

        other_code = next(code for code in codes if code != base_code)
        base_val = self.uc.to_base(12.5, other_code, "47")
        self.assertAlmostEqual(
            self.uc.convert(12.5, other_code, base_code, "47"),
            base_val,
            places=12,
        )
        self.assertAlmostEqual(
            self.uc.from_base(base_val, other_code, "47"),
            12.5,
            places=10,
        )
        self.assertEqual(self.uc.convert(7.25, other_code, other_code, "47"), 7.25)

    def test_returned_metadata_and_units_are_independent_copies(self) -> None:
        info = self.uc.get_parameter_info("0")
        info["name_RU"] = "Изменено"
        self.assertEqual(self.uc.get_parameter_info("0")["name_RU"], "Давление")

        units = self.uc.get_available_units("0")
        units[0]["ui"] = "MUTATED"
        units.clear()
        self.assertEqual(
            self.uc.get_available_units("0")[0],
            {"code": "кгс/см2", "ui": "кгс/см²"},
        )

    def test_legacy_keyword_arguments_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.uc.convert(10, from_unit="бар", to_unit="кгс/см2", parameter_type="0")


class TestUnknownIdAndNamesRejected(unittest.TestCase):
    def setUp(self) -> None:
        self.uc = UnitConverter()

    def _assert_unknown_id_uniform(self, bad_id) -> None:
        with self.assertRaises(UnknownParameterError):
            self.uc.get_parameter_info(bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.get_base_unit(bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.get_available_units(bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.to_base(1, "бар", bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.from_base(1, "бар", bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.convert(1, "бар", "МПа", bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.convert(1, "unknown", "unknown", bad_id)
        with self.assertRaises(UnknownParameterError):
            self.uc.add_unit(bad_id, unit_symbol="x", unit_name="X", to_base=1.0)

    def test_unknown_ids_raise_uniformly(self) -> None:
        for bad_id in ("999", "-1", "", "00", "48", " 0", 0, 47, None):
            with self.subTest(bad_id=bad_id):
                self._assert_unknown_id_uniform(bad_id)

    def test_name_ru_and_name_eng_rejected_instead_of_id(self) -> None:
        info_0 = self.uc.get_parameter_info("0")
        info_47 = self.uc.get_parameter_info("47")
        candidates = (
            info_0["name_RU"],
            info_0["name_ENG"],
            info_0["name_RU"].lower(),
            info_0["name_ENG"].lower(),
            info_47["name_RU"],
            info_47["name_ENG"],
        )
        for name_instead_of_id in candidates:
            with self.subTest(name=name_instead_of_id):
                self._assert_unknown_id_uniform(name_instead_of_id)

    def test_all_registry_names_rejected_for_lookup(self) -> None:
        for idx in range(48):
            info = self.uc.get_parameter_info(str(idx))
            for label in (info["name_RU"], info["name_ENG"]):
                with self.subTest(type_id=str(idx), label=label):
                    with self.assertRaises(UnknownParameterError):
                        self.uc.get_parameter_info(label)
                    with self.assertRaises(UnknownParameterError):
                        self.uc.get_base_unit(label)
                    with self.assertRaises(UnknownParameterError):
                        self.uc.get_available_units(label)


class TestUnknownUnits(unittest.TestCase):
    def setUp(self) -> None:
        self.uc = UnitConverter()

    def test_unknown_unit_codes_on_id_0_and_47(self) -> None:
        base_47 = self.uc.get_base_unit("47")
        cases = [
            ("0", "кгс/см2", ("unknown_unit", "C", "HB", "", None)),
            ("47", base_47, ("unknown_unit", "бар", "кгс/см2", "", None)),
        ]
        for type_id, valid_code, bad_codes in cases:
            for bad_code in bad_codes:
                with self.subTest(type_id=type_id, bad_code=bad_code):
                    with self.assertRaises(UnknownUnitError):
                        self.uc.to_base(10, bad_code, type_id)
                    with self.assertRaises(UnknownUnitError):
                        self.uc.from_base(10, bad_code, type_id)
                    with self.assertRaises(UnknownUnitError):
                        self.uc.convert(10, bad_code, valid_code, type_id)
                    with self.assertRaises(UnknownUnitError):
                        self.uc.convert(10, valid_code, bad_code, type_id)
                    with self.assertRaises(UnknownUnitError):
                        self.uc.convert(10, bad_code, bad_code, type_id)


class TestCodeVsUiSeparation(unittest.TestCase):
    def setUp(self) -> None:
        self.uc = UnitConverter()

    def test_ui_label_rejected_for_id_0(self) -> None:
        self.assertEqual(self.uc.convert(10, "кгс/см2", "кгс/см2", "0"), 10)
        for method_call in (
            lambda: self.uc.to_base(10, "кгс/см²", "0"),
            lambda: self.uc.from_base(10, "кгс/см²", "0"),
            lambda: self.uc.convert(10, "кгс/см²", "бар", "0"),
            lambda: self.uc.convert(10, "бар", "кгс/см²", "0"),
            lambda: self.uc.convert(10, "кгс/см²", "кгс/см²", "0"),
        ):
            with self.assertRaises(UnknownUnitError):
                method_call()

    def test_ui_labels_never_accepted_as_codes_across_registry(self) -> None:
        checked_pairs = 0
        for idx in range(48):
            type_id = str(idx)
            units = self.uc.get_available_units(type_id)
            codes = {u["code"] for u in units}
            base_code = self.uc.get_base_unit(type_id)
            for item in units:
                ui_label = item["ui"]
                if ui_label != item["code"] and ui_label not in codes:
                    checked_pairs += 1
                    with self.subTest(type_id=type_id, code=item["code"], ui=ui_label):
                        with self.assertRaises(UnknownUnitError):
                            self.uc.to_base(1, ui_label, type_id)
                        with self.assertRaises(UnknownUnitError):
                            self.uc.from_base(1, ui_label, type_id)
                        with self.assertRaises(UnknownUnitError):
                            self.uc.convert(1, ui_label, base_code, type_id)
                        with self.assertRaises(UnknownUnitError):
                            self.uc.convert(1, base_code, ui_label, type_id)
                        with self.assertRaises(UnknownUnitError):
                            self.uc.convert(1, ui_label, ui_label, type_id)
        self.assertGreater(checked_pairs, 0)

    def test_dynamic_unit_separates_code_and_display_label(self) -> None:
        self.uc.add_parameter(
            "48",
            parameter_name="Пользовательская скорость",
            parameter_name_eng="Custom velocity",
            base_unit_symbol="m/s",
            base_unit_name="Metre per second",
        )
        self.uc.add_unit(
            "48",
            unit_symbol="km/h",
            unit_name="Kilometre per hour",
            to_base=1 / 3.6,
            display_label="км/ч",
        )

        self.assertEqual(
            self.uc.get_available_units("48"),
            [{"code": "m/s", "ui": "m/s"}, {"code": "km/h", "ui": "км/ч"}],
        )
        self.assertAlmostEqual(self.uc.convert(36, "km/h", "m/s", "48"), 10.0, places=10)

        with self.assertRaises(UnknownUnitError):
            self.uc.to_base(36, "км/ч", "48")
        with self.assertRaises(UnknownUnitError):
            self.uc.from_base(10, "км/ч", "48")
        with self.assertRaises(UnknownUnitError):
            self.uc.convert(36, "км/ч", "m/s", "48")
        with self.assertRaises(UnknownUnitError):
            self.uc.convert(10, "m/s", "км/ч", "48")


if __name__ == "__main__":
    unittest.main()