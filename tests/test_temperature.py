import unittest

from uniconv import UnitConverter, UnknownUnitError


class TestTemperature(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_known_values_all_pairs(self):
        points = [dict(C=0, K=273.15, F=32, Re=0),
                  dict(C=100, K=373.15, F=212, Re=80),
                  dict(C=-40, K=233.15, F=-40, Re=-32),
                  dict(C=-273.15, K=0, F=-459.67, Re=-218.52)]
        for point in points:
            for source, value in point.items():
                for target, expected in point.items():
                    with self.subTest(point=point, source=source, target=target):
                        self.assertAlmostEqual(self.uc.convert(value, source, target, "1"), expected, delta=1e-10)
                        base = self.uc.to_base(value, source, "1")
                        self.assertAlmostEqual(base, point["C"], delta=1e-10)
                        self.assertAlmostEqual(self.uc.from_base(base, target, "1"), expected, delta=1e-10)

    def test_round_trip_and_exact_identity(self):
        for source in ("C", "K", "F", "Re"):
            for target in ("C", "K", "F", "Re"):
                for value in (-40, 0, 123.456):
                    converted = self.uc.convert(value, source, target, "1")
                    self.assertAlmostEqual(self.uc.convert(converted, target, source, "1"), value, delta=1e-5)
                    self.assertEqual(self.uc.convert(value, source, source, "1"), value)

    def test_codes_and_reaumur_label(self):
        self.assertEqual(self.uc.get_base_unit("1"), "C")
        self.assertIn({"code": "Re", "ui": "°Re"}, self.uc.get_available_units("1"))
        for code in ("°C", "°Re", "unknown"):
            with self.assertRaises(UnknownUnitError):
                self.uc.convert(1, code, "C", "1")
