import ast
import copy
import math
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import uniconv
from uniconv import constants as C
from uniconv import data_loader

FORBIDDEN_LITERALS: Set[float] = {
    9.80665,
    98066.5,
    98.0665,
    0.980665,
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


def _extract_numeric_literal(node: ast.AST):
    if isinstance(node, ast.Constant):
        value = node.value
    elif hasattr(ast, "Num") and isinstance(node, ast.Num):
        value = node.n
    else:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def find_forbidden_literals_in_python(
    package_dir: Path,
    allowed_filenames: Tuple[str, ...] = ("constants.py",),
    forbidden: Set[float] = FORBIDDEN_LITERALS,
) -> List[Tuple[Path, int, float]]:
    violations: List[Tuple[Path, int, float]] = []
    for path in sorted(package_dir.rglob("*.py")):
        if path.name in allowed_filenames:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            value = _extract_numeric_literal(node)
            if value is not None and value in forbidden:
                violations.append((path, getattr(node, "lineno", 0), value))
    return violations


def find_forbidden_literals_in_registry(
    registry: Dict[str, Any],
    forbidden: Set[float] = FORBIDDEN_LITERALS,
) -> List[Tuple[str, str, float, Any]]:
    violations: List[Tuple[str, str, float, Any]] = []
    for type_id, entry in registry.items():
        factors = entry.get("factors", {})
        for code, factor in factors.items():
            if isinstance(factor, (int, float)) and not isinstance(factor, bool):
                if factor in forbidden:
                    violations.append((type_id, code, factor, factor))
            elif isinstance(factor, str):
                source = re.sub(r"@([A-Z][A-Z0-9_]*)", r"\1", factor)
                tree = ast.parse(source, mode="eval")
                for node in ast.walk(tree):
                    value = _extract_numeric_literal(node)
                    if value is not None and value in forbidden:
                        violations.append((type_id, code, value, factor))
    return violations


def assert_no_magic_numbers(
    package_dir: Path,
    registry: Dict[str, Any],
    forbidden: Set[float] = FORBIDDEN_LITERALS,
) -> None:
    py_violations = find_forbidden_literals_in_python(
        package_dir, forbidden=forbidden)
    if py_violations:
        details = ", ".join(
            f"{path.name}:{lineno} ({val})" for path, lineno, val in py_violations
        )
        raise AssertionError(
            f"Обнаружены запрещённые литералы в Python-коде: {details}")

    reg_violations = find_forbidden_literals_in_registry(
        registry, forbidden=forbidden)
    if reg_violations:
        details = ", ".join(
            f"ID='{tid}' code='{code}' val={val} ({raw!r})"
            for tid, code, val, raw in reg_violations
        )
        raise AssertionError(
            f"Обнаружены запрещённые литералы в реестре JSON: {details}")


class TestMagicNumbers(unittest.TestCase):
    def test_library_python_files_have_no_forbidden_literals(self) -> None:
        package_dir = Path(uniconv.__file__).resolve().parent
        self.assertTrue((package_dir / "constants.py").is_file())
        violations = find_forbidden_literals_in_python(package_dir)
        self.assertEqual(
            violations,
            [],
            msg=f"Запрещённые числовые литералы вне uniconv/constants.py: {violations}",
        )

    def test_units_registry_has_no_forbidden_literals_and_valid_constant_refs(self) -> None:
        raw_registry = data_loader.load_json_resource("units_registry.json")
        violations = find_forbidden_literals_in_registry(raw_registry)
        self.assertEqual(
            violations,
            [],
            msg=f"Запрещённые числовые литералы в units_registry.json: {violations}",
        )

        referenced_constants: Set[str] = set()
        for entry in raw_registry.values():
            for factor in entry["factors"].values():
                if isinstance(factor, str) and "@" in factor:
                    referenced_constants.update(
                        re.findall(r"@([A-Z][A-Z0-9_]*)", factor))

        self.assertTrue(referenced_constants)
        for expected_ref in (
            "KGF_TO_N",
            "LBF_TO_N",
            "KGF_PER_CM2_TO_PA",
            "HP_METRIC_TO_W",
            "MMH2O_TO_PA",
        ):
            self.assertIn(expected_ref, referenced_constants)

    def test_g_standard_and_derived_constants_exist_in_constants_module(self) -> None:
        self.assertEqual(C.G_STANDARD, 9.80665)
        self.assertEqual(C.KGF_TO_N, C.G_STANDARD)
        self.assertEqual(C.LBF_TO_N, C.LB_TO_KG * C.G_STANDARD)
        self.assertEqual(C.HP_METRIC_TO_W, 75 * C.G_STANDARD)
        self.assertEqual(C.MMH2O_TO_PA, C.RHO_H2O_4C * C.G_STANDARD / 1000)
        self.assertEqual(C.KGF_PER_CM2_TO_PA, C.G_STANDARD * 1e4)

    def test_documented_test_data_excluded_while_algorithm_violation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "uniconv"
            pkg_dir.mkdir()
            (pkg_dir / "constants.py").write_text("G_STANDARD = 9.80665\n", encoding="utf-8")
            (pkg_dir / "algo.py").write_text(
                "from . import constants\n"
                "def to_n(val):\n"
                "    return val * constants.G_STANDARD\n",
                encoding="utf-8",
            )
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_sample.py").write_text("EXPECTED = 9.80665\n",
                                                      encoding="utf-8")

            raw_registry = data_loader.load_json_resource(
                "units_registry.json")
            assert_no_magic_numbers(pkg_dir, raw_registry)

            (pkg_dir / "algo.py").write_text(
                "def to_n(val):\n    return val * 9.80665\n",
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError) as ctx:
                assert_no_magic_numbers(pkg_dir, raw_registry)
            self.assertIn("algo.py", str(ctx.exception))
            self.assertIn("9.80665", str(ctx.exception))

    def test_registry_violation_fails_and_constant_ref_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "uniconv"
            pkg_dir.mkdir()
            (pkg_dir / "constants.py").write_text("G_STANDARD = 9.80665\n", encoding="utf-8")

            bad_numeric = copy.deepcopy(
                data_loader.load_json_resource("units_registry.json"))
            bad_numeric["0"]["factors"]["Па"] = 9.80665
            with self.assertRaises(AssertionError) as ctx_num:
                assert_no_magic_numbers(pkg_dir, bad_numeric)
            self.assertIn("ID='0'", str(ctx_num.exception))
            self.assertIn("Па", str(ctx_num.exception))
            self.assertIn("9.80665", str(ctx_num.exception))

            bad_expr = copy.deepcopy(
                data_loader.load_json_resource("units_registry.json"))
            bad_expr["20"]["factors"]["lbf"] = "@LB_TO_KG * 9.80665"
            with self.assertRaises(AssertionError) as ctx_expr:
                assert_no_magic_numbers(pkg_dir, bad_expr)
            self.assertIn("ID='20'", str(ctx_expr.exception))
            self.assertIn("lbf", str(ctx_expr.exception))
            self.assertIn("9.80665", str(ctx_expr.exception))

            valid_expr = copy.deepcopy(
                data_loader.load_json_resource("units_registry.json"))
            valid_expr["20"]["factors"]["lbf"] = "@LB_TO_KG * @G_STANDARD"
            assert_no_magic_numbers(pkg_dir, valid_expr)


if __name__ == "__main__":
    unittest.main()
