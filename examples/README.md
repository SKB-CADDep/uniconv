# Запускаемые примеры

Установите пакет и запустите скрипты из корня репозитория. Они используют импортируемую версию `uniconv` и не меняют файлы. Ключ `-X utf8` сохраняет русские подписи при перенаправлении вывода на Windows.

```console
python -m pip install "uniconv==2.0.0"
python -X utf8 examples/basic.py
python -X utf8 examples/presets.py
python -X utf8 examples/custom_units.py
```

- [basic.py](basic.py) — давление, температура и табличная конвертация твёрдости.
- [presets.py](presets.py) — хранение давления в базовой единице и показ по SI. Предупреждения об отброшенных парах — ожидаемое поведение.
- [custom_units.py](custom_units.py) — собственная величина и пользовательская единица.

[Вернуться к документации](../docs/README.md)
