"""Keep a value in base units and display it using a preset."""

from uniconv import UnitConverter


def main():
    uc = UnitConverter()
    type_id = "0"
    base_code = uc.get_base_unit(type_id)
    stored = uc.to_base(10, "бар", type_id)
    preset = uc.apply_preset("SI") or {}
    labels = {unit["code"]: unit["ui"] for unit in uc.get_available_units(type_id)}
    unit = preset.get(type_id, {"code": base_code, "ui": labels[base_code]})
    shown = uc.from_base(stored, unit["code"], type_id)
    print(f"Давление для отображения: {shown:g} {unit['ui']}")


if __name__ == "__main__":
    main()
