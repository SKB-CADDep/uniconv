import unittest

from uniconv import UnitConverter, UnknownUnitError


class TestTemperature(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_known_values_all_pairs(self):
        points = [
            dict(C=0, K=273.15, F=32, Re=0),
            dict(C=100, K=373.15, F=212, Re=80),
            dict(C=-40, K=233.15, F=-40, Re=-32),
            dict(C=-273.15, K=0, F=-459.67, Re=-218.52),
            dict(C=-300, K=-26.85, F=-508, Re=-240),
        ]
        for point in points:
            for source, value in point.items():
                for target, expected in point.items():
                    with self.subTest(point=point, source=source, target=target):
                        self.assertAlmostEqual(
                            self.uc.convert(value, source, target, "1"),
                            expected,
                            delta=1e-10,
                        )
                        base = self.uc.to_base(value, source, "1")
                        self.assertAlmostEqual(base, point["C"], delta=1e-10)
                        self.assertAlmostEqual(
                            self.uc.from_base(base, target, "1"),
                            expected,
                            delta=1e-10,
                        )

    def test_round_trip_and_exact_identity(self):
        for source in ("C", "K", "F", "Re"):
            for target in ("C", "K", "F", "Re"):
                for value in (-500.5, -273.15, -40, 0, 123.456):
                    with self.subTest(source=source, target=target, value=value):
                        converted = self.uc.convert(value, source, target, "1")
                        self.assertAlmostEqual(
                            self.uc.convert(converted, target, source, "1"),
                            value,
                            delta=1e-5,
                        )
                        self.assertEqual(self.uc.convert(
                            value, source, source, "1"), value)

    def test_codes_and_reaumur_label(self):
        self.assertEqual(self.uc.get_base_unit("1"), "C")
        units = self.uc.get_available_units("1")
        self.assertEqual([u["code"] for u in units], ["C", "K", "F", "Re"])
        self.assertIn({"code": "Re", "ui": "°Re"}, units)
        for code in ("°C", "°F", "°Re", "unknown"):
            with self.subTest(code=code):
                with self.assertRaises(UnknownUnitError):
                    self.uc.convert(1, code, "C", "1")
                with self.assertRaises(UnknownUnitError):
                    self.uc.to_base(1, code, "1")
                with self.assertRaises(UnknownUnitError):
                    self.uc.from_base(1, code, "1")
