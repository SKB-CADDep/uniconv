"""Load and validate bundled data independently of the working directory."""

import ast
import operator
import re
import json
import math
from importlib import resources

from .exceptions import DataLoadError
from . import constants


RESOURCE_NAMES = ("units_registry.json", "hardness_data.json", "presets.json")


def load_json_resource(name):
    """Read a bundled resource, preserving the cause of any loading error."""
    if name not in RESOURCE_NAMES:
        raise DataLoadError("Unknown resource: {!r}".format(name))
    try:
        if hasattr(resources, "files"):
            text = resources.files("uniconv").joinpath("data").joinpath(name).read_text(encoding="utf-8")
        else:  # Python 3.7 and 3.8
            text = resources.read_text("uniconv.data", name, encoding="utf-8")
        return json.loads(text)
    except (OSError, UnicodeError, ValueError) as exc:
        raise DataLoadError("Cannot load {}: {}".format(name, exc)) from exc


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)



_OPERATIONS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
               ast.Div: operator.truediv, ast.Pow: operator.pow}


def resolve_factor(expression):
    """Resolve @NAME and arithmetic over named constants, without eval.

    Only numeric literals, constant names, parentheses and + - * / ** are
    accepted. Attribute access, indexing and function calls are prohibited.
    """
    if not isinstance(expression, str) or "@" not in expression:
        return expression
    source = re.sub(r"@([A-Z][A-Z0-9_]*)", r"\1", expression)
    tree = ast.parse(source, mode="eval")

    def visit(node):
        if isinstance(node, ast.Constant):
            value = node.value
        elif isinstance(node, getattr(ast, "Num", ())):  # Python 3.7
            value = node.n
        elif isinstance(node, ast.Name):
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", node.id):
                raise ValueError("invalid constant name: {}".format(node.id))
            if not hasattr(constants, node.id):
                raise ValueError("unknown constant: {}".format(node.id))
            value = getattr(constants, node.id)
        elif isinstance(node, ast.BinOp) and type(node.op) in _OPERATIONS:
            value = _OPERATIONS[type(node.op)](visit(node.left), visit(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError("unsupported constant expression")
        if not _number(value):
            raise ValueError("constant expression must produce a finite number")
        return value

    return visit(tree.body)


def _resolve_registry(data):
    if not isinstance(data, dict):
        return
    for type_id, entry in data.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("factors"), dict):
            continue
        for code, factor in entry["factors"].items():
            try:
                entry["factors"][code] = resolve_factor(factor)
            except (ValueError, TypeError, SyntaxError, ArithmeticError) as exc:
                raise ValueError("{} / {}: {}".format(type_id, code, exc)) from exc


def _validate_registry(data):
    if not isinstance(data, dict) or set(data) != {str(i) for i in range(48)}:
        raise ValueError('registry must contain exactly the IDs "0" through "47"')
    for type_id, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError("{}: expected a parameter object".format(type_id))
        for field in ("name_RU", "name_ENG", "base_unit"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise ValueError("{}: missing or invalid {}".format(type_id, field))
        factors, labels = entry.get("factors"), entry.get("display_labels")
        if not isinstance(factors, dict) or not isinstance(labels, dict) or not factors:
            raise ValueError("{}: factors and display_labels must be nonempty objects".format(type_id))
        if set(factors) != set(labels) or not all(isinstance(v, str) and v for v in labels.values()):
            raise ValueError("{}: unit codes and UI labels must match".format(type_id))
        if any(not isinstance(code, str) or not code for code in factors):
            raise ValueError("{}: invalid unit code".format(type_id))
        if factors.get(entry["base_unit"]) != 1.0:
            raise ValueError("{}: base unit must have factor 1".format(type_id))
        markers = {"1": {"K": constants.OFFSET_K, "F": constants.OFFSET_F, "Re": constants.OFFSET_RE},
                   "34": {code: constants.TABLE for code in constants.HARDNESS_SCALES if code != "HB"}}
        for code, factor in factors.items():
            if code in markers.get(type_id, {}):
                if factor != markers[type_id][code]:
                    raise ValueError("{}: invalid algorithm marker for {}".format(type_id, code))
            elif not _number(factor) or factor <= 0:
                raise ValueError("{}: invalid factor for {}".format(type_id, code))
        if type_id == "1" and set(factors) != {"C", "K", "F", "Re"}:
            raise ValueError("temperature must define C, K, F and Re")
        if type_id == "34" and set(factors) != set(constants.HARDNESS_SCALES):
            raise ValueError("hardness must define all seven scales")


def _validate_hardness(data):
    if not isinstance(data, list) or not data:
        raise ValueError("hardness table must be a nonempty array")
    for row in data:
        if not isinstance(row, list) or len(row) != len(constants.HARDNESS_SCALES):
            raise ValueError("hardness rows must have seven columns: d10, HB, HRA, HRC, HRB, HV, HSD")
        if not _number(row[0]) or not _number(row[1]) or any(v is not None and not _number(v) for v in row):
            raise ValueError("hardness values must be finite numbers or null; d10 and HB are required")


def _validate_presets(data):
    if not isinstance(data, dict) or not isinstance(data.get("presets"), dict):
        raise ValueError("expected a presets object")
    for name, preset in data["presets"].items():
        if not isinstance(preset, dict) or not all(isinstance(preset.get(k), str) for k in ("name_RU", "name_ENG")):
            raise ValueError("{}: invalid preset metadata".format(name))
        units = preset.get("units")
        if not isinstance(units, dict) or any(not isinstance(code, str) for code in units.values()):
            raise ValueError("{}: units must map string IDs to string codes".format(name))
        # Referential validity belongs to apply_preset (DEV-08), not loading.


def load_data():
    """Return independently loaded registry, hardness rows and named presets."""
    loaded = []
    for name, validate in zip(RESOURCE_NAMES, (_validate_registry, _validate_hardness, _validate_presets)):
        data = load_json_resource(name)
        try:
            if name == "units_registry.json":
                _resolve_registry(data)
            validate(data)
        except (ValueError, TypeError, KeyError) as exc:
            raise DataLoadError("Invalid {}: {}".format(name, exc)) from exc
        loaded.append(data)
    return loaded[0], loaded[1], loaded[2]["presets"]
