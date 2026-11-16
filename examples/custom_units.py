"""Register a custom quantity and unit on one converter instance."""

from uniconv import UnitConverter


def main():
    uc = UnitConverter()
    uc.add_parameter(
        "48", base_unit_symbol="m/s", base_unit_name="метр в секунду",
        parameter_name="Пользовательская скорость",
    )
    uc.add_unit(
        "48", unit_symbol="km/h", unit_name="километр в час",
        to_base=1 / 3.6, display_label="км/ч",
    )
    speed = uc.convert(36, "km/h", "m/s", "48")
    print(f"36 км/ч → {speed:g} {uc.get_base_unit('48')}")


if __name__ == "__main__":
    main()
