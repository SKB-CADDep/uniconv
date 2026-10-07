import unittest

from uniconv import UnitConverter


class TestLinearConversion(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_every_linear_unit_formula_and_round_trip(self):
        for type_id, entry in self.uc.parameters.items():
            if type_id in ("1", "34"):
                continue
            base = entry["base_unit"]
            for code, factor in entry["factors"].items():
                for value in (-123.456, 0, 123.456):
                    with self.subTest(type_id=type_id, code=code, value=value):
                        converted = self.uc.convert(value, code, base, type_id)
                        self.assertEqual(converted, value * factor)
                        self.assertEqual(self.uc.to_base(value, code, type_id), converted)
                        self.assertEqual(self.uc.from_base(value, code, type_id), value / factor)
                        self.assertAlmostEqual(self.uc.convert(converted, base, code, type_id), value, delta=1e-5)
                        self.assertEqual(self.uc.convert(value, code, code, type_id), value)

    def test_nonbase_pairs_use_factor_ratio(self):
        self.assertEqual(self.uc.convert(10, "кВт", "Вт", "17"), 10000)
        self.assertAlmostEqual(self.uc.convert(1, "бар", "МПа", "0"), 0.1, delta=1e-5)
        self.assertAlmostEqual(self.uc.convert(100, "ккал/кг", "кДж/кг", "9"), 418.68, delta=0.001)
        self.assertEqual(self.uc.convert(0.88, "-", "%", "11"), 88)
        self.assertAlmostEqual(self.uc.convert(95, "%", "-", "11"), 0.95)
        self.assertAlmostEqual(self.uc.convert(1, "МВт", "Гкал/ч", "18"), 0.859845, delta=1e-6)
        self.assertAlmostEqual(self.uc.convert(1, "об/мин", "рад/с", "47"), 0.10472, delta=1e-6)

    def test_all_nonbase_pairs_round_trip(self):
        for type_id, entry in self.uc.parameters.items():
            if type_id in ("1", "34"):
                continue
            for source in entry["factors"]:
                for target in entry["factors"]:
                    with self.subTest(type_id=type_id, source=source, target=target):
                        result = self.uc.convert(123.456, source, target, type_id)
                        self.assertAlmostEqual(self.uc.convert(result, target, source, type_id), 123.456, delta=1e-5)
