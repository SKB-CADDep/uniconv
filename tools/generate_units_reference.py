#!/usr/bin/env python3
"""Generate the unit reference from the shipping registry, without dependencies."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "uniconv" / "data" / "units_registry.json"
OUTPUT = ROOT / "docs" / "units.md"


def code(value):
    return "`" + value + "`"


def cell(value):
    return value.replace("|", r"\|").replace("\n", " ")


def render():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = sorted(registry.items(), key=lambda item: int(item[0]))
    lines = [
        "# Справочник единиц",
        "",
        "[Все разделы](README.md) · [API](api.md)",
        "",
        "Страница генерируется из реестра UniConv. Передавайте строковый ID и точный код единицы.",
        "UI-метка предназначена для отображения; базовая единица не обязательно относится к СИ.",
        "",
        "| ID | Величина | Базовый код |",
        "|---|---|---|",
    ]
    for type_id, entry in entries:
        lines.append("| [{}](#id-{}) | {} | {} |".format(
            type_id, type_id, cell(entry["name_RU"]), code(cell(entry["base_unit"]))
        ))
    for type_id, entry in entries:
        lines.extend([
            "", "## ID {}".format(type_id), "",
            "**{}** ({}). Базовый код: {}.".format(
                entry["name_RU"], entry["name_ENG"], code(entry["base_unit"])
            ), "",
            "| Код для API | UI-метка |",
            "|---|---|",
        ])
        for unit in entry["factors"]:
            lines.append("| {} | {} |".format(
                code(cell(unit)), code(cell(entry["display_labels"][unit]))
            ))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the reference is outdated")
    args = parser.parse_args()
    rendered = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "Run python tools/generate_units_reference.py to update docs/units.md\n")
    else:
        OUTPUT.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
