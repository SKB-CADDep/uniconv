import json
import math
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Set

DATA_DIR = Path(__file__).resolve().parent.parent / "uniconv" / "data"

EXPECTED_PARAMETER_IDS: Set[str] = {str(i) for i in range(48)}
REQUIRED_PARAMETER_FIELDS = (
    "name_RU",
    "name_ENG",
    "base_unit",
    "factors",
    "display_labels",
)
NON_LINEAR_PARAMETER_IDS = {"1", "34"}
HARDNESS_ROW_COUNT = 441
HARDNESS_COLUMN_COUNT = 7
EXPECTED_PRESETS = ("SI", "TECH", "IMPERIAL")


def load_json_file(path: Path) -> Any:
    if not path.is_file():
        raise AssertionError(f"Отсутствует файл данных: {path}")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AssertionError(f"Не удалось прочитать файл {path.name} ({path}): {exc}") from exc
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Некорректный JSON в файле {path.name} "
            f"(строка {exc.lineno}, столбец {exc.colno}): {exc.msg}"
        ) from exc


def validate_units_registry(data: Any) -> None:
    if not isinstance(data, dict):
        raise AssertionError(
            f"units_registry.json должен содержать JSON-объект, получено: {type(data).__name__}"
        )

    actual_ids = set(data.keys())
    missing_ids = sorted(EXPECTED_PARAMETER_IDS - actual_ids, key=int)
    if missing_ids:
        raise AssertionError(f"В units_registry.json отсутствуют ID: {missing_ids}")

    unexpected_ids = sorted(actual_ids - EXPECTED_PARAMETER_IDS)
    if unexpected_ids:
        raise AssertionError(f"В units_registry.json обнаружены лишние ID: {unexpected_ids}")

    for param_id in sorted(EXPECTED_PARAMETER_IDS, key=int):
        entry = data[param_id]
        if not isinstance(entry, dict):
            raise AssertionError(
                f"Величина ID='{param_id}' должна быть JSON-объектом, "
                f"получено: {type(entry).__name__}"
            )

        missing_fields = [field for field in REQUIRED_PARAMETER_FIELDS if field not in entry]
        if missing_fields:
            raise AssertionError(
                f"У величины ID='{param_id}' отсутствуют обязательные поля: {missing_fields}"
            )

        for text_field in ("name_RU", "name_ENG", "base_unit"):
            value = entry[text_field]
            if not isinstance(value, str) or not value.strip():
                raise AssertionError(
                    f"У величины ID='{param_id}' поле '{text_field}' должно быть непустой строкой"
                )

        factors = entry["factors"]
        display_labels = entry["display_labels"]

        if not isinstance(factors, dict) or not factors:
            raise AssertionError(
                f"У величины ID='{param_id}' поле 'factors' должно быть непустым словарём"
            )
        if not isinstance(display_labels, dict) or not display_labels:
            raise AssertionError(
                f"У величины ID='{param_id}' поле 'display_labels' должно быть непустым словарём"
            )

        base_unit = entry["base_unit"]
        if base_unit not in factors:
            raise AssertionError(
                f"У величины ID='{param_id}' базовая единица '{base_unit}' отсутствует в 'factors'"
            )

        factor_keys = set(factors.keys())
        label_keys = set(display_labels.keys())

        missing_labels = sorted(factor_keys - label_keys)
        if missing_labels:
            raise AssertionError(
                f"У величины ID='{param_id}' отсутствуют UI-метки в 'display_labels' "
                f"для единиц: {missing_labels}"
            )

        extra_labels = sorted(label_keys - factor_keys)
        if extra_labels:
            raise AssertionError(
                f"У величины ID='{param_id}' в 'display_labels' есть лишние ключи, "
                f"отсутствующие в 'factors': {extra_labels}"
            )

        for unit_code, factor in factors.items():
            if not isinstance(unit_code, str) or not unit_code.strip():
                raise AssertionError(
                    f"У величины ID='{param_id}' найден некорректный код единицы: {unit_code!r}"
                )

            ui_label = display_labels[unit_code]
            if not isinstance(ui_label, str) or not ui_label.strip():
                raise AssertionError(
                    f"У величины ID='{param_id}' пустая или некорректная UI-метка "
                    f"для единицы '{unit_code}': {ui_label!r}"
                )

            if factor is None:
                if param_id not in NON_LINEAR_PARAMETER_IDS:
                    raise AssertionError(
                        f"У величины ID='{param_id}' коэффициент для '{unit_code}' не может быть null"
                    )
            elif isinstance(factor, bool):
                raise AssertionError(
                    f"У величины ID='{param_id}' коэффициент для '{unit_code}' не может быть bool"
                )
            elif isinstance(factor, (int, float)):
                if not math.isfinite(factor):
                    raise AssertionError(
                        f"У величины ID='{param_id}' некорректное число для '{unit_code}': {factor}"
                    )
                if param_id not in NON_LINEAR_PARAMETER_IDS and factor <= 0:
                    raise AssertionError(
                        f"У величины ID='{param_id}' коэффициент для '{unit_code}' "
                        f"должен быть > 0, получено: {factor}"
                    )
            elif isinstance(factor, str):
                if not factor.strip():
                    raise AssertionError(
                        f"У величины ID='{param_id}' пустое строковое выражение для '{unit_code}'"
                    )
            else:
                raise AssertionError(
                    f"У величины ID='{param_id}' неподдерживаемый тип коэффициента "
                    f"для '{unit_code}': {type(factor).__name__}"
                )


def validate_hardness_data(data: Any) -> None:
    if not isinstance(data, list):
        raise AssertionError(
            f"hardness_data.json должен содержать JSON-массив строк, получено: {type(data).__name__}"
        )

    if len(data) != HARDNESS_ROW_COUNT:
        raise AssertionError(
            f"hardness_data.json должен содержать {HARDNESS_ROW_COUNT} строк, "
            f"получено: {len(data)}"
        )

    for row_idx, row in enumerate(data):
        if not isinstance(row, list):
            raise AssertionError(
                f"Строка {row_idx} в hardness_data.json должна быть массивом, "
                f"получено: {type(row).__name__}"
            )
        if len(row) != HARDNESS_COLUMN_COUNT:
            raise AssertionError(
                f"Строка {row_idx} в hardness_data.json должна содержать {HARDNESS_COLUMN_COUNT} "
                f"колонок [d10, HB, HRA, HRC, HRB, HV, HSD], получено: {len(row)}"
            )
        for col_idx, cell in enumerate(row):
            if cell is None:
                if col_idx in (0, 1):
                    raise AssertionError(
                        f"Обязательная колонка {col_idx} (d10/HB) в hardness_data.json "
                        f"[{row_idx}] не может быть null"
                    )
                continue
            if isinstance(cell, bool) or not isinstance(cell, (int, float)):
                raise AssertionError(
                    f"Некорректное значение в hardness_data.json [{row_idx}][{col_idx}]: {cell!r}"
                )
            if not math.isfinite(cell):
                raise AssertionError(
                    f"Неконечное число в hardness_data.json [{row_idx}][{col_idx}]: {cell!r}"
                )


def validate_presets(data: Any) -> None:
    if not isinstance(data, dict):
        raise AssertionError(
            f"presets.json должен содержать JSON-объект, получено: {type(data).__name__}"
        )

    if "presets" not in data or not isinstance(data["presets"], dict):
        raise AssertionError("presets.json должен содержать объект 'presets'")

    presets = data["presets"]
    for preset_name in EXPECTED_PRESETS:
        if preset_name not in presets:
            raise AssertionError(f"В presets.json отсутствует обязательный пресет '{preset_name}'")

    for preset_name, preset in presets.items():
        if not isinstance(preset_name, str) or not preset_name.strip():
            raise AssertionError(f"Некорректное имя пресета в presets.json: {preset_name!r}")
        if not isinstance(preset, dict):
            raise AssertionError(
                f"Пресет '{preset_name}' в presets.json должен быть JSON-объектом"
            )

        for meta_field in ("name_RU", "name_ENG"):
            meta_value = preset.get(meta_field)
            if not isinstance(meta_value, str) or not meta_value.strip():
                raise AssertionError(
                    f"У пресета '{preset_name}' поле '{meta_field}' должно быть непустой строкой"
                )

        units = preset.get("units")
        if not isinstance(units, dict) or not units:
            raise AssertionError(
                f"У пресета '{preset_name}' поле 'units' должно быть непустым JSON-объектом"
            )

        for param_id, unit_code in units.items():
            if not isinstance(param_id, str) or not param_id.strip():
                raise AssertionError(
                    f"В пресете '{preset_name}' некорректный ID величины: {param_id!r}"
                )
            if not isinstance(unit_code, str) or not unit_code.strip():
                raise AssertionError(
                    f"В пресете '{preset_name}' для ID='{param_id}' "
                    f"указан некорректный код единицы: {unit_code!r}"
                )


class TestDataFiles(unittest.TestCase):
    def test_units_registry_file(self) -> None:
        data = load_json_file(DATA_DIR / "units_registry.json")
        validate_units_registry(data)

    def test_hardness_data_file(self) -> None:
        data = load_json_file(DATA_DIR / "hardness_data.json")
        validate_hardness_data(data)

    def test_presets_file(self) -> None:
        data = load_json_file(DATA_DIR / "presets.json")
        validate_presets(data)


class TestDataValidationDiagnostics(unittest.TestCase):
    @staticmethod
    def _make_minimal_valid_registry() -> Dict[str, Dict[str, Any]]:
        return {
            str(i): {
                "name_RU": f"Параметр {i}",
                "name_ENG": f"Parameter {i}",
                "base_unit": "u0",
                "factors": {"u0": 1, "u1": 2},
                "display_labels": {"u0": "u0", "u1": "u1"},
            }
            for i in range(48)
        }

    def test_missing_file_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "units_registry.json"
            with self.assertRaises(AssertionError) as ctx:
                load_json_file(missing)
            self.assertIn("units_registry.json", str(ctx.exception))

    def test_invalid_json_syntax_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broken = Path(tmpdir) / "broken.json"
            broken.write_text('{"0": invalid_json}', encoding="utf-8")
            with self.assertRaises(AssertionError) as ctx:
                load_json_file(broken)
            self.assertIn("broken.json", str(ctx.exception))
            self.assertIn("строка 1", str(ctx.exception))

    def test_missing_id_detected(self) -> None:
        registry = self._make_minimal_valid_registry()
        del registry["47"]
        with self.assertRaises(AssertionError) as ctx:
            validate_units_registry(registry)
        self.assertIn("47", str(ctx.exception))

    def test_missing_required_field_detected(self) -> None:
        registry = self._make_minimal_valid_registry()
        del registry["0"]["base_unit"]
        with self.assertRaises(AssertionError) as ctx:
            validate_units_registry(registry)
        self.assertIn("ID='0'", str(ctx.exception))
        self.assertIn("base_unit", str(ctx.exception))

    def test_missing_ui_label_detected(self) -> None:
        registry = self._make_minimal_valid_registry()
        del registry["5"]["display_labels"]["u1"]
        with self.assertRaises(AssertionError) as ctx:
            validate_units_registry(registry)
        self.assertIn("ID='5'", str(ctx.exception))
        self.assertIn("u1", str(ctx.exception))

    def test_invalid_hardness_row_detected(self) -> None:
        rows = [[1.0] * HARDNESS_COLUMN_COUNT for _ in range(HARDNESS_ROW_COUNT)]
        rows[10] = [1.0, 2.0]
        with self.assertRaises(AssertionError) as ctx:
            validate_hardness_data(rows)
        self.assertIn("Строка 10", str(ctx.exception))

    def test_missing_preset_detected(self) -> None:
        presets = {
            "presets": {
                "SI": {"name_RU": "СИ", "name_ENG": "SI", "units": {"0": "МПа"}},
                "TECH": {"name_RU": "Тех.", "name_ENG": "Tech", "units": {"0": "кгс/см2"}},
            }
        }
        with self.assertRaises(AssertionError) as ctx:
            validate_presets(presets)
        self.assertIn("IMPERIAL", str(ctx.exception))

    def test_missing_presets_wrapper_detected(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            validate_presets({"SI": {}})
        self.assertIn("presets", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()