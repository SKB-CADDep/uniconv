"""Convert pressure, temperature and hardness with the installed package."""

from uniconv import UnitConverter


def main():
    uc = UnitConverter()
    pressure = uc.convert(10, "бар", "МПа", "0")
    temperature = uc.convert(212, "F", "C", "1")
    hardness = uc.convert(709, "HB", "HV", "34")

    print(f"10 бар → {pressure:g} МПа")
    print(f"212 °F → {temperature:g} °C")
    if hardness is not None:
        print(f"709 HB → {hardness:g} HV")
    else:
        print("Для указанной твёрдости нет табличных данных")


if __name__ == "__main__":
    main()
