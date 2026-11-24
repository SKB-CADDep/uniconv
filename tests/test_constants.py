import ast
import math
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import uniconv
from uniconv import DataLoadError, UnitConverter, constants as C
from uniconv import data_loader


def _numeric_ast_value(node):
    if isinstance(node, ast.Constant):
        value = node.value
    elif hasattr(ast, "Num") and isinstance(node, ast.Num):
        value = node.n
    else:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


class TestConstants(unittest.TestCase):
    def test_required_constants_and_definitions(self):
        required = (
            "PI",
            "E",
            "TWO_PI",
            "DEG_TO_RAD",
            "RAD_TO_DEG",
            "G_STANDARD",
            "STANDARD_ATMOSPHERE",
            "KGF_TO_N",
            "LB_TO_KG",
            "LBF_TO_N",
            "HP_METRIC_TO_W",
            "HP_TO_W",
            "ATM_TO_PA",
            "MMHG_TO_PA",
            "MM_HG_TO_PA",
            "MMH2O_TO_PA",
            "KGF_PER_CM2_TO_PA",
            "T_PER_H_TO_KG_PER_S",
            "RHO_H2O_4C",
            "RHO_HG_0C",
            "INCH_TO_MM",
            "FOOT_TO_MM",
            "YARD_TO_MM",
            "MILE_TO_MM",
            "CAL_TO_J",
            "LIGHT_YEAR_TO_MM",
            "MINUTE_TO_S",
            "HOUR_TO_S",
            "DAY_TO_S",
            "YEAR_365D_TO_S",
            "CELSIUS_TO_KELVIN_OFFSET",
            "FAHRENHEIT_OFFSET",
            "FAHRENHEIT_RATIO",
            "FAHRENHEIT_RATIO_INV",
            "REAUMUR_TO_CELSIUS",
            "CELSIUS_TO_REAUMUR",
        )
        for name in required:
            self.assertTrue(math.isfinite(getattr(C, name)), name)

        self.assertEqual(C.PI, math.pi)
        self.assertEqual(C.E, math.e)
        self.assertEqual(C.TWO_PI, 2 * C.PI)
        self.assertEqual(C.DEG_TO_RAD, C.PI / 180)
        self.assertEqual(C.RAD_TO_DEG, 180 / C.PI)

        self.assertEqual(C.G_STANDARD, 9.80665)
        self.assertEqual(C.KGF_TO_N, C.G_STANDARD)
        self.assertEqual(C.LB_TO_KG, 0.45359237)
        self.assertEqual(C.LBF_TO_N, C.LB_TO_KG * C.G_STANDARD)
        self.assertAlmostEqual(C.LBF_TO_N, 4.4482216152605, places=13)
        self.assertEqual(C.HP_METRIC_TO_W, 75 * C.G_STANDARD)
        self.assertEqual(C.HP_TO_W, C.HP_METRIC_TO_W)
        self.assertAlmostEqual(C.HP_METRIC_TO_W, 735.49875, places=10)
        self.assertEqual(C.MMH2O_TO_PA, C.RHO_H2O_4C * C.G_STANDARD / 1000)
        self.assertEqual(C.KGF_PER_CM2_TO_PA, C.G_STANDARD * 1e4)

        self.assertEqual(C.STANDARD_ATMOSPHERE, 101325.0)
        self.assertEqual(C.ATM_TO_PA, C.STANDARD_ATMOSPHERE)
        self.assertEqual(C.MMHG_TO_PA, 133.322387415)
        self.assertEqual(C.MM_HG_TO_PA, C.MMHG_TO_PA)
        self.assertEqual(C.INCH_TO_MM, 25.4)
        self.assertEqual(C.FOOT_TO_MM, 304.8)
        self.assertEqual(C.YARD_TO_MM, 914.4)
        self.assertEqual(C.MILE_TO_MM, 1609344.0)
        self.assertEqual(C.CAL_TO_J, 4.1868)
        self.assertEqual(C.LIGHT_YEAR_TO_MM, 9.4607e18)
        self.assertEqual(C.CELSIUS_TO_KELVIN_OFFSET, 273.15)
        self.assertEqual(C.T_PER_H_TO_KG_PER_S, 1000 / C.HOUR_TO_S)

    def test_resolution_and_cached_numeric_factors(self):
        self.assertEqual(data_loader.resolve_factor(
            "@G_STANDARD"), C.G_STANDARD)
        self.assertEqual(data_loader.resolve_factor(
            "@KGF_TO_N / 100"), C.G_STANDARD / 100)
        uc = UnitConverter()
        old = uc.convert(1, "Па", "кгс/см2", "0")
        with patch.object(C, "KGF_PER_CM2_TO_PA", 1):
            self.assertEqual(uc.convert(1, "Па", "кгс/см2", "0"), old)
        for type_id, entry in uc.parameters.items():
            if type_id not in ("1", "34"):
                self.assertTrue(
                    all(isinstance(v, (int, float))
                        for v in entry["factors"].values())
                )

    def test_unsafe_unknown_and_invalid_expressions_are_diagnostic(self):
        for expression in (
            "@MISSING",
            "@TABLE",
            "@G_STANDARD / 0",
            "@G_STANDARD.real",
            "@G_STANDARD[0]",
            "@G_STANDARD + abs(-1)",
            "@G_STANDARD + True",
            "@G_STANDARD +",
        ):
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
        self.assertAlmostEqual(uc.convert(
            1, "psi", "Па", "0"), 6894.757293168, places=8)
        self.assertAlmostEqual(uc.convert(1, "л.с.", "Вт", "17"), 735.49875)
        self.assertAlmostEqual(uc.convert(
            1, "lbf", "Н", "20"), 4.4482216152605)
        for type_id in ("36", "37", "38", "39", "40", "41"):
            self.assertAlmostEqual(uc.convert(
                1, "кгс/мм2", "МПа", type_id), 9.80665)
        self.assertAlmostEqual(uc.convert(
            1, "кгс*м/см2", "кДж/м2", "42"), 98.0665)
        self.assertAlmostEqual(uc.convert(
            1, "Н/см4", "кгс/см4", "46"), 1 / 9.80665)
        self.assertAlmostEqual(uc.convert(
            1, "радианы", "град", "30"), 180 / math.pi)
        self.assertAlmostEqual(uc.convert(
            1, "об/мин", "рад/с", "47"), 2 * math.pi / 60)

    def test_no_forbidden_literals_outside_constants(self):
        forbidden = {
            9.80665,
            98066.5,
            98.0665,
            0.0980665,
            0.00980665,
            0.45359237,
            4.44822,
            4.4482216152605,
            273.15,
            101325,
            133.322387415,
            735.49875,
            735.499,
            25.4,
            3.14159,
            3.141592653589793,
            9.4607e18,
        }
        package = Path(uniconv.__file__).resolve().parent
        for path in package.rglob("*.py"):
            if path.name == "constants.py":
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                value = _numeric_ast_value(node)
                if value is not None:
                    self.assertNotIn(value, forbidden, str(path))

        raw = data_loader.load_json_resource("units_registry.json")
        for type_id, entry in raw.items():
            for code, factor in entry["factors"].items():
                if isinstance(factor, (int, float)) and not isinstance(factor, bool):
                    self.assertNotIn(factor, forbidden, (type_id, code))
                elif isinstance(factor, str):
                    source = re.sub(r"@([A-Z][A-Z0-9_]*)", r"\1", factor)
                    for node in ast.walk(ast.parse(source, mode="eval")):
                        value = _numeric_ast_value(node)
                        if value is not None:
                            self.assertNotIn(value, forbidden, (type_id, code))
