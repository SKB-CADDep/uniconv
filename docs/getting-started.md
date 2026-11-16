# Быстрый старт

[Все разделы](README.md) · [API](api.md) · [Единицы](units.md)

Создайте виртуальное окружение проекта. На Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "uniconv==2.0.0"
```

На Linux и macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install "uniconv==2.0.0"
```

Если окружение уже активировано:

```console
python -m pip install "uniconv==2.0.0"
```

Если работаете с клоном репозитория, выполните `python -m pip install .` в его корне. Один экземпляр можно использовать для многих вызовов: реестр, константы и таблица твёрдости подготавливаются при создании `UnitConverter()`.

```python
from uniconv import UnitConverter

uc = UnitConverter()
pressure = uc.convert(value=10, from_u="бар", to_u="МПа", type_id="0")
assert pressure == 1.0
```

1. Найдите ID величины в [справочнике](units.md): например, `"0"` — давление, `"1"` — температура, `"24"` — длина.
2. Выберите исходную и целевую единицы из одной величины. Используйте точные коды, включая регистр и пробелы.
3. Передайте число и коды в `convert()`. Округление для отображения задавайте в приложении.

```python
from uniconv import UnitConverter

uc = UnitConverter()
info = uc.get_parameter_info("0")
assert info["base_unit"] == "кгс/см2"

units = {entry["code"]: entry["ui"] for entry in uc.get_available_units("0")}
assert units["кгс/см2"] == "кгс/см²"
value = uc.convert(10, "бар", "кгс/см2", "0")
print(f"{value:.3f} {units['кгс/см2']}")  # 10.197 кгс/см²
```

Для формы выбора храните `code` в значении поля, а `ui` показывайте пользователю. Локализованное имя величины и целочисленный ID `0` вместо строки `"0"` не принимаются.

```python
from uniconv import UnitConverter, UnknownParameterError, UnknownUnitError

uc = UnitConverter()
try:
    uc.convert(10, "бар", "°C", "0")
except UnknownParameterError:
    print("Неизвестный ID величины")
except UnknownUnitError:
    print("Код единицы не зарегистрирован для выбранной величины")
```

`DataLoadError` при создании объекта означает, что данные пакета отсутствуют или повреждены. Для твёрдости допустимые ID и коды ещё не гарантируют, что есть табличные данные: проверяйте результат через `is None`.


## Если пример не запускается

- `ModuleNotFoundError: No module named 'uniconv'`: установите пакет тем же интерпретатором, которым запускаете скрипт. Команда `python -m pip show uniconv` показывает версию и путь установки.
- `UnknownUnitError`: сравните значение с полем `code` из `get_available_units(type_id)`. Например, для температуры используется `C`, хотя в интерфейсе показано `°C`.
- При перенаправлении вывода на Windows запускайте примеры через `python -X utf8`, чтобы сохранить кириллицу и обозначения единиц.
