import math
import unittest

from uniconv import UnitConverter

HARDNESS_COLUMNS = ("d10", "HB", "HRA", "HRC", "HRB", "HV", "HSD")


class TestAllParameters(unittest.TestCase):
    def setUp(self) -> None:
        self.uc = UnitConverter()

    def _check_hardness_parameter(self, type_id: str, base_unit: str, units: list) -> None:
        self.assertEqual(
            base_unit, "HB", msg=f"ID={type_id!r}, base_unit={base_unit!r}")
        scale_to_col = {name: idx for idx, name in enumerate(HARDNESS_COLUMNS)}

        for item in units:
            unit_code = item["code"]
            with self.subTest(type_id=type_id, base_unit=base_unit, unit_code=unit_code):
                col_idx = scale_to_col[unit_code]
                row = next(
                    (r for r in self.uc.hardness_data if r[1]
                     is not None and r[col_idx] is not None),
                    None,
                )
                self.assertIsNotNone(
                    row,
                    msg=(
                        f"Не найдена табличная строка для ID={type_id!r}, "
                        f"base_unit={base_unit!r}, unit_code={unit_code!r}"
                    ),
                )
                hb_value = row[1]

                converted = self.uc.convert(
                    hb_value, base_unit, unit_code, type_id)
                from_base_val = self.uc.from_base(hb_value, unit_code, type_id)
                self.assertIsNotNone(
                    converted,
                    msg=f"Прямая конвертация вернула None для ID={type_id!r}, {base_unit!r} -> {unit_code!r}",
                )
                self.assertEqual(
                    converted,
                    from_base_val,
                    msg=f"Несовпадение convert и from_base для ID={type_id!r}, {base_unit!r} -> {unit_code!r}",
                )
                self.assertTrue(
                    math.isfinite(converted),
                    msg=f"Неконечный результат для ID={type_id!r}, {base_unit!r} -> {unit_code!r}: {converted!r}",
                )

                restored = self.uc.convert(
                    converted, unit_code, base_unit, type_id)
                to_base_val = self.uc.to_base(converted, unit_code, type_id)
                self.assertIsNotNone(
                    restored,
                    msg=f"Обратная конвертация вернула None для ID={type_id!r}, {unit_code!r} -> {base_unit!r}",
                )
                self.assertEqual(
                    restored,
                    to_base_val,
                    msg=f"Несовпадение convert и to_base для ID={type_id!r}, {unit_code!r} -> {base_unit!r}",
                )
                self.assertTrue(
                    math.isfinite(restored),
                    msg=f"Неконечный обратный результат для ID={type_id!r}, {unit_code!r} -> {base_unit!r}: {restored!r}",
                )

                if unit_code == base_unit:
                    self.assertEqual(
                        restored,
                        hb_value,
                        msg=f"Нарушена точность самоконвертации для ID={type_id!r}, unit={unit_code!r}",
                    )

        self.assertEqual(
            self.uc.convert(709, "HB", "HV", type_id),
            1007.5,
            msg=f"ID={type_id!r}, 'HB' -> 'HV'",
        )
        self.assertEqual(
            self.uc.convert(1007.5, "HV", "HB", type_id),
            709,
            msg=f"ID={type_id!r}, 'HV' -> 'HB'",
        )

    def _check_parameter(self, type_id: str) -> None:
        info = self.uc.get_parameter_info(type_id)
        self.assertEqual(
            info["id"], type_id, msg=f"Неверный id в метаданных для ID={type_id!r}")

        base_unit = self.uc.get_base_unit(type_id)
        self.assertTrue(
            isinstance(base_unit, str) and base_unit,
            msg=f"Пустая базовая единица для ID={type_id!r}",
        )
        self.assertEqual(
            base_unit,
            info["base_unit"],
            msg=f"Несовпадение get_base_unit и get_parameter_info для ID={type_id!r}, base_unit={base_unit!r}",
        )

        units = self.uc.get_available_units(type_id)
        self.assertGreater(
            len(units), 0, msg=f"Нет доступных единиц для ID={type_id!r}")
        codes = [item["code"] for item in units]
        self.assertIn(
            base_unit,
            codes,
            msg=f"Базовая единица {base_unit!r} отсутствует в get_available_units для ID={type_id!r}",
        )

        self.assertEqual(
            self.uc.convert(100.0, base_unit, base_unit, type_id),
            100.0,
            msg=f"Нарушена самоконвертация базовой единицы для ID={type_id!r}, base_unit={base_unit!r}",
        )

        if type_id == "34":
            self._check_hardness_parameter(type_id, base_unit, units)
            return

        test_value = 100.0
        for unit_code in codes:
            with self.subTest(type_id=type_id, base_unit=base_unit, unit_code=unit_code):
                converted = self.uc.convert(
                    test_value, base_unit, unit_code, type_id)
                from_base_val = self.uc.from_base(
                    test_value, unit_code, type_id)
                self.assertAlmostEqual(
                    converted,
                    from_base_val,
                    delta=1e-5,
                    msg=(
                        f"Несовпадение convert и from_base для ID={type_id!r}, "
                        f"base_unit={base_unit!r}, unit_code={unit_code!r}"
                    ),
                )

                restored = self.uc.convert(
                    converted, unit_code, base_unit, type_id)
                to_base_val = self.uc.to_base(converted, unit_code, type_id)
                self.assertAlmostEqual(
                    restored,
                    test_value,
                    delta=1e-5,
                    msg=(
                        f"Нарушена обратимость convert для ID={type_id!r}, "
                        f"base_unit={base_unit!r}, unit_code={unit_code!r}"
                    ),
                )
                self.assertAlmostEqual(
                    to_base_val,
                    test_value,
                    delta=1e-5,
                    msg=(
                        f"Нарушена обратимость to_base(from_base) для ID={type_id!r}, "
                        f"base_unit={base_unit!r}, unit_code={unit_code!r}"
                    ),
                )


def _make_parameter_test(type_id: str):
    def test_method(self: TestAllParameters) -> None:
        self._check_parameter(type_id)

    test_method.__name__ = f"test_parameter_{int(type_id):02d}"
    test_method.__doc__ = f"Verify base unit and round-trip conversion for ID {type_id!r}."
    return test_method


for _idx in range(48):
    setattr(TestAllParameters,
            f"test_parameter_{_idx:02d}", _make_parameter_test(str(_idx)))


if __name__ == "__main__":
    unittest.main()
