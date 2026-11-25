import ast
import copy
import hashlib
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

import uniconv
from uniconv import (
    DataLoadError,
    UnitConverter,
    UnknownParameterError,
    UnknownUnitError,
    constants,
)

LEGACY_KWARGS = {"parameter_type", "from_unit", "to_unit"}
DATA_FILES = ("units_registry.json", "hardness_data.json", "presets.json")


def _is_typeerror_assert_context(node: ast.With) -> bool:
    for item in node.items:
        expr = item.context_expr
        if not isinstance(expr, ast.Call):
            continue
        func = expr.func
        func_name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if func_name in ("assertRaises", "raises") and expr.args:
            arg0 = expr.args[0]
            if isinstance(arg0, ast.Name) and arg0.id == "TypeError":
                return True
    return False


def _find_legacy_api_calls(tree: ast.AST, in_typeerror_ctx: bool = False) -> List[Tuple[int, str]]:
    found: List[Tuple[int, str]] = []
    if isinstance(tree, ast.With) and _is_typeerror_assert_context(tree):
        in_typeerror_ctx = True
    if isinstance(tree, ast.Call) and not in_typeerror_ctx:
        for kw in tree.keywords:
            if kw.arg in LEGACY_KWARGS:
                found.append((getattr(tree, "lineno", 0), kw.arg))
    for child in ast.iter_child_nodes(tree):
        found.extend(_find_legacy_api_calls(child, in_typeerror_ctx))
    return found


class TestRegression(unittest.TestCase):
    def test_package_exports_and_import_independent_of_cwd(self) -> None:
        mod = importlib.import_module("uniconv")
        self.assertIs(mod.UnitConverter, UnitConverter)
        self.assertIs(mod.UnknownParameterError, UnknownParameterError)
        self.assertIs(mod.UnknownUnitError, UnknownUnitError)
        self.assertIs(mod.DataLoadError, DataLoadError)
        self.assertIs(mod.constants, constants)

        prev_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                uc = UnitConverter()
                self.assertAlmostEqual(uc.convert(10, "бар", "МПа", "0"), 1.0, places=12)
                self.assertAlmostEqual(uc.convert(100, "C", "Re", "1"), 80.0, places=12)
                self.assertEqual(uc.convert(709, "HB", "HV", "34"), 1007.5)
            finally:
                os.chdir(prev_cwd)

    def test_conversions_do_not_modify_json_files_or_loaded_data(self) -> None:
        data_dir = Path(uniconv.__file__).resolve().parent / "data"
        hashes_before = {
            name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
            for name in DATA_FILES
        }

        uc = UnitConverter()
        snapshot_params = copy.deepcopy(uc.parameters)
        snapshot_hardness = copy.deepcopy(uc.hardness_data)
        snapshot_presets = copy.deepcopy(uc.presets)

        _ = uc.convert(10, "бар", "кгс/см2", "0")
        _ = uc.to_base(10, "бар", "0")
        _ = uc.from_base(1.0, "МПа", "0")
        _ = uc.convert(212, "F", "C", "1")
        _ = uc.convert(709, "HB", "HV", "34")
        _ = uc.convert(100, "HRB", "HB", "34")
        _ = uc.get_parameter_info("0")
        _ = uc.get_available_units("0")
        _ = uc.get_preset("SI")
        _ = uc.apply_preset("SI")

        self.assertEqual(uc.parameters, snapshot_params)
        self.assertEqual(uc.hardness_data, snapshot_hardness)
        self.assertEqual(uc.presets, snapshot_presets)

        uc.add_parameter(
            "48",
            parameter_name="Тест",
            parameter_name_eng="Test",
            base_unit_symbol="u0",
            base_unit_name="U0",
        )
        uc.add_unit("48", unit_symbol="u1", unit_name="U1", to_base=2.0)
        _ = uc.convert(5, "u1", "u0", "48")

        hashes_after = {
            name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
            for name in DATA_FILES
        }
        self.assertEqual(hashes_before, hashes_after)

    def test_reinitialization_produces_identical_results_after_mutations(self) -> None:
        uc1 = UnitConverter()
        uc2 = UnitConverter()

        uc1.add_parameter(
            "48",
            parameter_name="Тест",
            parameter_name_eng="Test",
            base_unit_symbol="m/s",
            base_unit_name="Metre per second",
        )
        uc1.add_unit("48", unit_symbol="km/h", unit_name="Kilometre per hour", to_base=1 / 3.6)
        uc1.parameters["0"]["factors"]["бар"] = 999.0
        uc1.hardness_data[0][5] = -1.0
        uc1.presets["custom"] = {"units": {"0": "Па"}}

        uc3 = UnitConverter()

        for fresh in (uc2, uc3):
            self.assertAlmostEqual(fresh.convert(10, "бар", "МПа", "0"), 1.0, places=12)
            self.assertAlmostEqual(fresh.convert(373.15, "K", "C", "1"), 100.0, places=12)
            self.assertEqual(fresh.convert(712, "HB", "HV", "34"), 1016)
            self.assertEqual(fresh.list_presets(), ["SI", "TECH", "IMPERIAL"])
            self.assertNotIn("custom", fresh.list_presets())
            with self.assertRaises(UnknownParameterError):
                fresh.get_parameter_info("48")

    def test_execution_order_independence(self) -> None:
        forward = UnitConverter()
        forward_results = (
            forward.convert(10, "бар", "кгс/см2", "0"),
            forward.convert(212, "F", "C", "1"),
            forward.convert(709, "HB", "HV", "34"),
            forward.convert(1, "об/мин", "рад/с", "47"),
            forward.get_preset("SI"),
        )

        reverse = UnitConverter()
        preset_rev = reverse.get_preset("SI")
        res_47 = reverse.convert(1, "об/мин", "рад/с", "47")
        res_34 = reverse.convert(709, "HB", "HV", "34")
        res_1 = reverse.convert(212, "F", "C", "1")
        res_0 = reverse.convert(10, "бар", "кгс/см2", "0")
        reverse_results = (res_0, res_1, res_34, res_47, preset_rev)

        self.assertEqual(forward_results, reverse_results)

    def test_no_positive_legacy_api_calls_in_tests(self) -> None:
        tests_dir = Path(__file__).resolve().parent
        violations = []
        for path in sorted(tests_dir.glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for lineno, kw in _find_legacy_api_calls(tree):
                violations.append(f"{path.name}:{lineno} ({kw})")
        self.assertEqual(
            violations,
            [],
            msg=f"Обнаружены вызовы устаревшего API в тестах: {violations}",
        )


if __name__ == "__main__":
    unittest.main()