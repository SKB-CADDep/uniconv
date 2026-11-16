# Практические сценарии

[Все разделы](README.md) · [API](api.md) · [Примеры](../examples/README.md)

## Хранение в базовой единице и показ по пресету

Сохраните число вместе с ID и кодом базовой единицы. Для отображения выберите код из пресета; отсутствующую пару можно заменить базовой единицей. Не нужно менять сохранённые данные при смене пользовательских настроек.

```python
from uniconv import UnitConverter

uc = UnitConverter()
type_id = "0"
base_code = uc.get_base_unit(type_id)
stored = uc.to_base(10, "бар", type_id)

si = uc.apply_preset("SI") or {}
unit_labels = {item["code"]: item["ui"] for item in uc.get_available_units(type_id)}
display = si.get(type_id, {"code": base_code, "ui": unit_labels[base_code]})
shown = uc.from_base(stored, display["code"], type_id)
assert shown == 1.0
print(f"{shown:g} {display['ui']}")  # 1 МПа
```

В исходных пресетах есть пары с несуществующими кодами. `apply_preset()` пропускает их с предупреждениями, а `get_preset()` сохраняет исходные пары. Предупреждение при применении встроенного пресета ожидаемо.

## Температура и твёрдость

Точные коды шкал температуры — `C`, `K`, `F`, `Re`. Твёрдость использует шкалы `d10`, `HB`, `HRA`, `HRC`, `HRB`, `HV`, `HSD`.

```python
from uniconv import UnitConverter

uc = UnitConverter()
assert uc.convert(0, "C", "K", "1") == 273.15
assert uc.convert(212, "F", "Re", "1") == 80.0

assert uc.convert(712, "HB", "HV", "34") == 1016
assert uc.convert(709, "HB", "HV", "34") == 1007.5
assert uc.convert(713, "HB", "HV", "34") is None
assert uc.convert(712, "HB", "HRB", "34") is None
```

Для твёрдости библиотека интерполирует между соседними точками внутри участка с данными. Она не экстраполирует за пределы участка и не интерполирует через пропуски. При повторяющихся исходных значениях используется первая подходящая строка; табличное преобразование не всегда обратимо. При преобразовании шкалы в себя возвращается исходное число.

## Пользовательская величина

```python
from math import isclose
from uniconv import UnitConverter

uc = UnitConverter()
uc.add_parameter(
    "48", base_unit_symbol="m/s", base_unit_name="метр в секунду",
    parameter_name="Пользовательская скорость", parameter_name_eng="Custom velocity",
)
uc.add_unit(
    "48", unit_symbol="km/h", unit_name="километр в час",
    to_base=1 / 3.6, display_label="км/ч",
)
assert isclose(uc.convert(36, "km/h", "m/s", "48"), 10)
```

Для нелинейной единицы можно передать две функции. В следующем условном примере показание датчика смещено на 10 мм относительно длины:

```python
from uniconv import UnitConverter

uc = UnitConverter()
uc.add_unit(
    "24", unit_symbol="sensor-mm", unit_name="показание датчика",
    to_base=lambda reading: reading - 10,
    from_base=lambda length: length + 10,
)
assert uc.convert(35, "sensor-mm", "мм", "24") == 25
assert uc.convert(25, "мм", "sensor-mm", "24") == 35
```

Пользовательские единицы не записываются в JSON. Регистрируйте их при создании каждого экземпляра, которому они нужны.
