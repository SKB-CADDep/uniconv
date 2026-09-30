import ast
import copy
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from uniconv import DataLoadError, UnitConverter
from uniconv import data_loader


class TestExternalData(unittest.TestCase):
    def setUp(self):
        self.registry, self.hardness, self.presets = data_loader.load_data()

    def test_registry_structure(self):
        self.assertEqual(set(self.registry), {str(i) for i in range(48)})
        for type_id, entry in self.registry.items():
            with self.subTest(type_id=type_id):
                self.assertTrue({"name_RU", "name_ENG", "base_unit", "factors", "display_labels"} <= set(entry))
                self.assertEqual(set(entry["factors"]), set(entry["display_labels"]))
                self.assertEqual(entry["factors"][entry["base_unit"]], 1)

    def test_data_matches_full_specification_appendices(self):
        spec = Path(__file__).resolve().parents[1] / "docs" / "uniconv.md"
        blocks = re.findall(r"```(?:JSON|json|Python|python)?\s*\n(.*?)```", spec.read_text(encoding="utf-8"), re.S)
        original = json.loads(blocks[1])
        for type_id, entry in original.items():
            for code, factor in entry["factors"].items():
                raw = data_loader.load_json_resource("units_registry.json")[type_id]["factors"][code]
                if not isinstance(raw, str) or "@" not in raw:
                    self.assertEqual(self.registry[type_id]["factors"][code], factor)
        self.assertEqual(self.hardness, ast.literal_eval(blocks[2]))
        self.assertEqual(self.presets, json.loads(blocks[3])["presets"])
        self.assertEqual(len(self.hardness), 441)
        self.assertEqual(self.hardness[0], [2.30, 712, 85.1, 66.4, None, 1016, 98.3])
        self.assertEqual(self.hardness[-1][0], 6.70)
        self.assertEqual({len(row) for row in self.hardness}, {7})
        self.assertEqual(set(self.presets), {"SI", "TECH", "IMPERIAL"})

    def test_json_is_standard_and_no_shared_data(self):
        for name in data_loader.RESOURCE_NAMES:
            self.assertIsInstance(data_loader.load_json_resource(name), (dict, list))
        first, second = UnitConverter(), UnitConverter()
        first.hardness_data[0][0] = 99
        first.presets["SI"]["units"]["0"] = "changed"
        self.assertEqual(second.hardness_data[0][0], 2.3)
        self.assertEqual(second.presets["SI"]["units"]["0"], "МПа")

    def test_missing_corrupt_and_invalid_encoding_resources(self):
        for error in (FileNotFoundError("missing"), PermissionError("denied"), UnicodeError("bad encoding")):
            with patch.object(data_loader.resources, "files", side_effect=error, create=True):
                with self.assertRaises(DataLoadError) as result:
                    UnitConverter()
                self.assertIn("units_registry.json", str(result.exception))
                self.assertIs(result.exception.__cause__, error)
        with patch.object(data_loader.resources, "files", create=True) as files:
            files.return_value.joinpath.return_value.joinpath.return_value.read_text.return_value = "{broken"
            with self.assertRaises(DataLoadError) as result:
                UnitConverter()
            self.assertIn("units_registry.json", str(result.exception))
            self.assertIsInstance(result.exception.__cause__, json.JSONDecodeError)

    def test_invalid_shapes_diagnostic(self):
        invalid_registry = copy.deepcopy(self.registry)
        del invalid_registry["0"]["display_labels"]["Па"]
        cases = [(0, {}), (0, invalid_registry), (1, [[1, 2]]),
                 (1, [[1, 2, None, None, None, float("nan"), None]]), (2, {"presets": []})]
        valid = [self.registry, self.hardness, {"presets": self.presets}]
        for index, invalid in cases:
            values = copy.deepcopy(valid)
            values[index] = invalid
            with patch.object(data_loader, "load_json_resource", side_effect=values):
                with self.assertRaises(DataLoadError) as result:
                    UnitConverter()
                self.assertIn(data_loader.RESOURCE_NAMES[index], str(result.exception))
                self.assertIsNotNone(result.exception.__cause__)

    def test_legacy_resource_api(self):
        # Exercise the Python 3.7/3.8 loading branch on the current interpreter.
        with patch.object(data_loader, "hasattr",
                          side_effect=lambda obj, name: False if obj is data_loader.resources and name == "files" else hasattr(obj, name),
                          create=True):
            self.assertEqual(data_loader.load_data(), (self.registry, self.hardness, self.presets))
