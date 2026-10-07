import unittest

from uniconv import UnitConverter, UnknownUnitError
from uniconv.hardness import HardnessConverter


class TestHardness(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_exact_first_row_all_scales(self):
        point = {"d10": 2.3, "HB": 712, "HRA": 85.1, "HRC": 66.4, "HV": 1016, "HSD": 98.3}
        for source, value in point.items():
            for target, expected in point.items():
                with self.subTest(source=source, target=target):
                    self.assertAlmostEqual(self.uc.convert(value, source, target, "34"), expected)

    def test_hrb_scale(self):
        self.assertEqual(self.uc.convert(100, "HRB", "HB", "34"), 244)
        self.assertEqual(self.uc.convert(244, "HB", "HRB", "34"), 100)

    def test_interpolation_both_directions(self):
        self.assertAlmostEqual(self.uc.convert(709, "HB", "HV", "34"), 1007.5)
        self.assertAlmostEqual(self.uc.convert(1007.5, "HV", "HB", "34"), 709)
        self.assertAlmostEqual(self.uc.convert(2.305, "d10", "HV", "34"), 1007.5)
        self.assertAlmostEqual(self.uc.convert(1007.5, "HV", "d10", "34"), 2.305)

    def test_ranges_missing_scales_and_nonfinite(self):
        for value, source, target in ((713, "HB", "HV"), (74, "HB", "HV"),
                                      (1017, "HV", "HB"), (2.29, "d10", "HB"),
                                      (6.71, "d10", "HB"), (712, "HB", "HRB"),
                                      (float("nan"), "HV", "HB"), (float("inf"), "HB", "HV")):
            self.assertIsNone(self.uc.convert(value, source, target, "34"))
        self.assertEqual(self.uc.convert(75, "HB", "HB", "34"), 75)
        self.assertEqual(self.uc.convert(6.70, "d10", "HB", "34"), 75)
        with self.assertRaises(UnknownUnitError):
            self.uc.convert(1, "bad", "HB", "34")

    def test_null_breaks_intervals_and_no_extrapolation(self):
        rows = [[1, 100, None, None, None, 10, None],
                [2, 200, None, None, None, 20, None],
                [3, 300, None, None, None, None, None],
                [4, 400, None, None, None, 40, None]]
        table = HardnessConverter(rows)
        self.assertEqual(table.from_base(150, "HV"), 15)
        self.assertEqual(table.to_base(15, "HV"), 150)
        self.assertIsNone(table.from_base(300, "HV"))
        self.assertIsNone(table.to_base(30, "HV"))
        self.assertEqual(table.from_base(400, "HV"), 40)
        self.assertIsNone(table.from_base(450, "HV"))
        self.assertIsNone(table.from_base(200, "HRC"))

    def test_duplicate_source_values_are_deterministic(self):
        rows = [[1, 100, None, None, None, 10, None],
                [2, 100, None, None, None, 11, None],
                [3, 200, None, None, None, 20, None]]
        table = HardnessConverter(rows)
        self.assertEqual(table.from_base(100, "HV"), 10)
        self.assertEqual(table.to_base(11, "HV"), 100)
        self.assertEqual(table.from_base(150, "HV"), 15)
