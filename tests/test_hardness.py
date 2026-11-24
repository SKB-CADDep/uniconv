import unittest

from uniconv import UnitConverter, UnknownUnitError
from uniconv.hardness import HardnessConverter

HARDNESS_COLUMNS = ("d10", "HB", "HRA", "HRC", "HRB", "HV", "HSD")


class TestHardness(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_exact_first_row_all_scales(self):
        point = {
            "d10": 2.3,
            "HB": 712,
            "HRA": 85.1,
            "HRC": 66.4,
            "HV": 1016,
            "HSD": 98.3,
        }
        for source, value in point.items():
            for target, expected in point.items():
                with self.subTest(source=source, target=target):
                    self.assertAlmostEqual(
                        self.uc.convert(value, source, target, "34"),
                        expected,
                    )

    def test_exact_boundary_rows_all_scales(self):
        self.assertEqual(self.uc.convert(75, "HB", "d10", "34"), 6.67)
        self.assertEqual(self.uc.convert(6.67, "d10", "HB", "34"), 75)
        self.assertEqual(self.uc.convert(6.70, "d10", "HB", "34"), 75)

        for col_idx, scale in enumerate(HARDNESS_COLUMNS):
            non_null_rows = [
                r for r in self.uc.hardness_data if r[col_idx] is not None]
            self.assertTrue(non_null_rows)
            unambiguous_rows = [
                r
                for r in non_null_rows
                if all(
                    other[col_idx] is not None
                    for other in self.uc.hardness_data
                    if other[1] == r[1]
                )
            ]
            self.assertTrue(unambiguous_rows)
            for edge_row in (unambiguous_rows[0], unambiguous_rows[-1]):
                with self.subTest(scale=scale, hb=edge_row[1], val=edge_row[col_idx]):
                    self.assertIsNotNone(self.uc.convert(
                        edge_row[1], "HB", scale, "34"))
                    self.assertIsNotNone(self.uc.convert(
                        edge_row[col_idx], scale, "HB", "34"))

    def test_hrb_scale(self):
        self.assertEqual(self.uc.convert(100, "HRB", "HB", "34"), 244)
        self.assertEqual(self.uc.convert(244, "HB", "HRB", "34"), 100)
        self.assertEqual(self.uc.to_base(100, "HRB", "34"), 244)
        self.assertEqual(self.uc.from_base(244, "HRB", "34"), 100)

    def test_interpolation_both_directions(self):
        self.assertAlmostEqual(self.uc.convert(709, "HB", "HV", "34"), 1007.5)
        self.assertAlmostEqual(self.uc.convert(1007.5, "HV", "HB", "34"), 709)
        self.assertAlmostEqual(self.uc.from_base(709, "HV", "34"), 1007.5)
        self.assertAlmostEqual(self.uc.to_base(1007.5, "HV", "34"), 709)
        self.assertAlmostEqual(self.uc.convert(
            2.305, "d10", "HV", "34"), 1007.5)
        self.assertAlmostEqual(self.uc.convert(
            1007.5, "HV", "d10", "34"), 2.305)

    def test_ranges_missing_scales_and_nonfinite(self):
        out_of_range_cases = (
            (713, "HB", "HV"),
            (74, "HB", "HV"),
            (1017, "HV", "HB"),
            (2.29, "d10", "HB"),
            (6.71, "d10", "HB"),
            (712, "HB", "HRB"),
            (float("nan"), "HV", "HB"),
            (float("inf"), "HB", "HV"),
            (float("-inf"), "HB", "HV"),
        )
        for value, source, target in out_of_range_cases:
            with self.subTest(value=value, source=source, target=target):
                self.assertIsNone(self.uc.convert(value, source, target, "34"))

        self.assertIsNone(self.uc.from_base(713, "HV", "34"))
        self.assertIsNone(self.uc.to_base(1017, "HV", "34"))
        self.assertIsNone(self.uc.from_base(712, "HRB", "34"))

        for col_idx, scale in enumerate(HARDNESS_COLUMNS):
            values = [r[col_idx]
                      for r in self.uc.hardness_data if r[col_idx] is not None]
            below_min = min(values) - 1.0
            above_max = max(values) + 1.0
            with self.subTest(scale=scale, below_min=below_min, above_max=above_max):
                if scale != "HB":
                    self.assertIsNone(self.uc.convert(
                        below_min, scale, "HB", "34"))
                    self.assertIsNone(self.uc.convert(
                        above_max, scale, "HB", "34"))
                else:
                    self.assertIsNone(self.uc.convert(
                        below_min, "HB", "d10", "34"))
                    self.assertIsNone(self.uc.convert(
                        above_max, "HB", "d10", "34"))

            hbs_with_value = {
                r[1] for r in self.uc.hardness_data if r[col_idx] is not None}
            hbs_only_null = sorted(
                {r[1] for r in self.uc.hardness_data if r[col_idx]
                    is None} - hbs_with_value
            )
            if hbs_only_null:
                self.assertIsNone(self.uc.convert(
                    hbs_only_null[0], "HB", scale, "34"))
                self.assertIsNone(self.uc.convert(
                    hbs_only_null[-1], "HB", scale, "34"))

        self.assertEqual(self.uc.convert(75, "HB", "HB", "34"), 75)
        self.assertEqual(self.uc.convert(9999, "HB", "HB", "34"), 9999)
        self.assertEqual(self.uc.convert(-10, "HV", "HV", "34"), -10)
        self.assertEqual(self.uc.convert(500, "HRB", "HRB", "34"), 500)
        self.assertEqual(self.uc.convert(6.70, "d10", "HB", "34"), 75)

        for bad_call in (
            lambda: self.uc.convert(1, "bad", "HB", "34"),
            lambda: self.uc.convert(1, "bad", "bad", "34"),
            lambda: self.uc.to_base(1, "bad", "34"),
            lambda: self.uc.from_base(1, "bad", "34"),
        ):
            with self.assertRaises(UnknownUnitError):
                bad_call()

    def test_null_breaks_intervals_and_no_extrapolation(self):
        rows = [
            [1, 100, None, None, None, 10, None],
            [2, 200, None, None, None, 20, None],
            [3, 300, None, None, None, None, None],
            [4, 400, None, None, None, 40, None],
        ]
        table = HardnessConverter(rows)
        self.assertEqual(table.from_base(150, "HV"), 15)
        self.assertEqual(table.to_base(15, "HV"), 150)

        self.assertIsNone(table.from_base(250, "HV"))
        self.assertIsNone(table.to_base(25, "HV"))
        self.assertIsNone(table.from_base(300, "HV"))
        self.assertIsNone(table.to_base(30, "HV"))
        self.assertIsNone(table.from_base(350, "HV"))
        self.assertIsNone(table.to_base(35, "HV"))

        self.assertEqual(table.from_base(400, "HV"), 40)
        self.assertIsNone(table.from_base(50, "HV"))
        self.assertIsNone(table.to_base(5, "HV"))
        self.assertIsNone(table.from_base(450, "HV"))
        self.assertIsNone(table.to_base(45, "HV"))
        self.assertIsNone(table.from_base(200, "HRC"))

    def test_duplicate_source_values_are_deterministic(self):
        rows = [
            [1, 100, None, None, None, 10, None],
            [2, 100, None, None, None, 11, None],
            [3, 200, None, None, None, 20, None],
        ]
        table = HardnessConverter(rows)
        self.assertEqual(table.from_base(100, "HV"), 10)
        self.assertEqual(table.to_base(11, "HV"), 100)
        self.assertEqual(table.from_base(150, "HV"), 15)
