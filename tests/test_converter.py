import unittest

from uniconv import UnitConverter, UnknownParameterError, UnknownUnitError


class TestUnitConverter(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_metadata_and_extreme_ids(self):
        for type_id in ("0", "47"):
            info = self.uc.get_parameter_info(type_id)
            self.assertEqual(set(info), {"id", "name_RU", "name_ENG", "base_unit"})
            self.assertEqual(info["id"], type_id)
            self.assertEqual(self.uc.get_base_unit(type_id), info["base_unit"])
        self.assertEqual(self.uc.get_base_unit("0"), "кгс/см2")
        self.assertEqual(self.uc.get_base_unit("47"), "1/с")

    def test_available_units_code_ui_and_isolation(self):
        units = self.uc.get_available_units("0")
        self.assertEqual(units[0], {"code": "кгс/см2", "ui": "кгс/см²"})
        self.assertEqual([u["code"] for u in units], list(self.uc.parameters["0"]["factors"]))
        units[0]["ui"] = "changed"
        info = self.uc.get_parameter_info("0")
        info["name_RU"] = "changed"
        self.assertEqual(self.uc.get_available_units("0")[0]["ui"], "кгс/см²")
        self.assertEqual(self.uc.get_parameter_info("0")["name_RU"], "Давление")

    def test_unknown_id_is_uniform(self):
        for type_id in ("unknown", "pressure", "Pressure", "Давление", " 0", "00", 0, None, []):
            calls = [lambda: self.uc.convert(1, "Па", "МПа", type_id),
                     lambda: self.uc.to_base(1, "Па", type_id),
                     lambda: self.uc.from_base(1, "Па", type_id),
                     lambda: self.uc.get_available_units(type_id),
                     lambda: self.uc.get_parameter_info(type_id),
                     lambda: self.uc.get_base_unit(type_id),
                     lambda: self.uc.add_unit(type_id, unit_symbol="x", unit_name="X", to_base=1)]
            for call in calls:
                with self.subTest(type_id=type_id, call=call):
                    with self.assertRaises(UnknownParameterError):
                        call()

    def test_unknown_codes_and_ui_labels(self):
        for from_u, to_u in (("missing", "Па"), ("Па", "missing"),
                             ("кгс/см²", "Па"), ("Па", "°C"), ("missing", "missing")):
            with self.assertRaises(UnknownUnitError):
                self.uc.convert(1, from_u, to_u, "0")
        with self.assertRaises(UnknownUnitError):
            self.uc.to_base(1, "missing", "0")
        with self.assertRaises(UnknownUnitError):
            self.uc.from_base(1, "missing", "0")

    def test_dynamic_addition_and_instance_isolation(self):
        other = UnitConverter()
        self.uc.add_parameter("48", parameter_name="Скорость пользователя", parameter_name_eng="Custom velocity",
                              base_unit_symbol="m/s", base_unit_name="Metre per second")
        self.uc.add_unit("48", unit_symbol="km/h", unit_name="Kilometre per hour", to_base=1/3.6)
        self.assertAlmostEqual(self.uc.convert(36, "km/h", "m/s", "48"), 10)
        self.assertAlmostEqual(self.uc.convert(20, "m/s", "km/h", "48"), 72)
        self.assertNotIn("48", other.parameters)
        self.uc.add_unit("0", unit_symbol="custom", unit_name="Custom", to_base=2, display_label="Custom UI")
        self.assertNotIn("custom", other.parameters["0"]["factors"])
        self.assertIn({"code": "custom", "ui": "Custom UI"}, self.uc.get_available_units("0"))
        with self.assertRaises(ValueError):
            self.uc.add_parameter("48", parameter_name="Duplicate", base_unit_symbol="m/s", base_unit_name="Metre")
        with self.assertRaises(ValueError):
            self.uc.add_parameter("speed", parameter_name="Bad ID", base_unit_symbol="m/s", base_unit_name="Metre")

    def test_dynamic_functions_and_explicit_inverse(self):
        self.uc.add_unit("24", unit_symbol="shifted", unit_name="Shifted", to_base=lambda v: v + 10,
                         from_base=lambda v: v - 10)
        self.assertEqual(self.uc.convert(5, "shifted", "мм", "24"), 15)
        self.assertEqual(self.uc.convert(15, "мм", "shifted", "24"), 5)
        self.uc.add_unit("24", unit_symbol="double", unit_name="Double", to_base=2, from_base=0.5)
        self.assertEqual(self.uc.convert(12, "double", "shifted", "24"), 14)
        with self.assertRaises(ValueError):
            self.uc.add_unit("24", unit_symbol="bad", unit_name="Bad", to_base=lambda v: v)
        for factor in (0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.uc.add_unit("24", unit_symbol="bad", unit_name="Bad", to_base=factor)
        self.assertNotIn("bad", self.uc.parameters["24"]["factors"])
        with self.assertRaises(ValueError):
            self.uc.add_unit("24", unit_symbol="мм", unit_name="Base", to_base=2)

    def test_hardness_is_not_treated_as_linear(self):
        self.assertEqual(self.uc.convert(200, "HB", "HB", "34"), 200)
        self.assertEqual(self.uc.convert(712, "HB", "HV", "34"), 1016)
        self.assertIsNone(self.uc.convert(200, "HRC", "HV", "34"))
        self.assertEqual(self.uc.to_base(1016, "HV", "34"), 712)
        self.assertEqual(self.uc.from_base(712, "HV", "34"), 1016)


if __name__ == "__main__":
    unittest.main()
