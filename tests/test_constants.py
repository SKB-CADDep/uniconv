import ast
import json
import math
import unittest
from pathlib import Path
from unittest.mock import patch

import uniconv
from uniconv import UnitConverter, DataLoadError, constants as C
from uniconv import data_loader


class TestConstants(unittest.TestCase):
    def test_required_constants_and_definitions(self):
        required = ("PI", "E", "TWO_PI", "DEG_TO_RAD", "RAD_TO_DEG", "G_STANDARD",
                    "KGF_TO_N", "LB_TO_KG", "LBF_TO_N", "HP_METRIC_TO_W", "ATM_TO_PA",
                    "MMHG_TO_PA", "RHO_H2O_4C", "RHO_HG_0C", "INCH_TO_MM", "FOOT_TO_MM",
                    "YARD_TO_MM", "MILE_TO_MM", "CAL_TO_J", "LIGHT_YEAR_TO_MM", "MINUTE_TO_S",
                    "HOUR_TO_S", "DAY_TO_S", "YEAR_365D_TO_S", "FAHRENHEIT_OFFSET",
                    "FAHRENHEIT_RATIO", "FAHRENHEIT_RATIO_INV", "REAUMUR_TO_CELSIUS", "CELSIUS_TO_REAUMUR")
        for name in required:
            self.assertTrue(math.isfinite(getattr(C, name)), name)
        self.assertEqual(C.PI, math.pi)
        self.assertEqual(C.E, math.e)
        self.assertEqual(C.KGF_TO_N, 9.80665)
        self.assertEqual(C.LB_TO_KG, 0.45359237)
        self.assertAlmostEqual(C.LBF_TO_N, 4.4482216152605, places=13)
        self.assertAlmostEqual(C.HP_METRIC_TO_W, 735.49875, places=10)
        self.assertEqual(C.MMHG_TO_PA, 133.322387415)
        self.assertEqual(C.INCH_TO_MM, 25.4)

    def test_resolution_and_cached_numeric_factors(self):
        self.assertEqual(data_loader.resolve_factor("@G_STANDARD"), C.G_STANDARD)
        self.assertEqual(data_loader.resolve_factor("@KGF_TO_N / 100"), C.G_STANDARD / 100)
        uc = UnitConverter()
        old = uc.convert(1, "Па", "кгс/см2", "0")
        with patch.object(C, "KGF_PER_CM2_TO_PA", 1):
            self.assertEqual(uc.convert(1, "Па", "кгс/см2", "0"), old)
        for type_id, entry in uc.parameters.items():
            if type_id not in ("1", "34"):
                self.assertTrue(all(isinstance(v, (int, float)) for v in entry["factors"].values()))

    def test_unsafe_unknown_and_invalid_expressions_are_diagnostic(self):
        for expression in ("@MISSING", "@TABLE", "@G_STANDARD / 0", "@G_STANDARD.real",
                           "@G_STANDARD[0]", "@G_STANDARD + abs(-1)", "@G_STANDARD + True", "@G_STANDARD +"):
            data = data_loader.load_json_resource("units_registry.json")
            data["0"]["factors"]["Па"] = expression
            with patch.object(data_loader, "load_json_resource", return_value=data):
                with self.assertRaises(DataLoadError) as result:
                    UnitConverter()
            message = str(result.exception)
            self.assertIn("units_registry.json", message)
            self.assertIn("0 / Па", message)

    def test_gravity_dependent_conversions(self):
        uc = UnitConverter()
        self.assertAlmostEqual(uc.convert(1, "кгс/см2", "Па", "0"), 98066.5)
        self.assertAlmostEqual(uc.convert(1, "psi", "Па", "0"), 6894.757293168, places=8)
        self.assertAlmostEqual(uc.convert(1, "л.с.", "Вт", "17"), 735.49875)
        self.assertAlmostEqual(uc.convert(1, "lbf", "Н", "20"), 4.4482216152605)
        for type_id in ("36", "37", "38", "39", "40", "41"):
            self.assertAlmostEqual(uc.convert(1, "кгс/мм2", "МПа", type_id), 9.80665)
        self.assertAlmostEqual(uc.convert(1, "кгс*м/см2", "кДж/м2", "42"), 98.0665)
        self.assertAlmostEqual(uc.convert(1, "Н/см4", "кгс/см4", "46"), 1 / 9.80665)
        self.assertAlmostEqual(uc.convert(1, "радианы", "град", "30"), 180 / math.pi)
        self.assertAlmostEqual(uc.convert(1, "об/мин", "рад/с", "47"), 2 * math.pi / 60)

    def test_no_forbidden_literals_outside_constants(self):
        forbidden = {9.80665, 0.45359237, 273.15, 101325, 133.322387415, 735.49875,
                     4.44822, 25.4, 0.0980665, 0.00980665, 735.499}
        package = Path(uniconv.__file__).resolve().parent
        for path in package.rglob("*.py"):
            if path.name == "constants.py":
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                value = getattr(node, "value", getattr(node, "n", None))
                if isinstance(value, (int, float)):
                    self.assertNotIn(value, forbidden, str(path))
        raw = data_loader.load_json_resource("units_registry.json")
        for type_id, entry in raw.items():
            for code, factor in entry["factors"].items():
                if isinstance(factor, (int, float)):
                    self.assertNotIn(factor, forbidden, (type_id, code))
                elif "@" in factor:
                    source = __import__("re").sub(r"@([A-Z][A-Z0-9_]*)", r"\1", factor)
                    for node in ast.walk(ast.parse(source, mode="eval")):
                        value = getattr(node, "value", getattr(node, "n", None))
                        if isinstance(value, (int, float)):
                            self.assertNotIn(value, forbidden, (type_id, code))
