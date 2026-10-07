"""ID-based conversion using the external engineering units registry."""

from __future__ import annotations

import copy
import logging
import math
from typing import Callable, Union, Optional, Dict, List, Any

from . import constants as const
from .data_loader import load_data
from .hardness import HardnessConverter
from .exceptions import UnknownParameterError, UnknownUnitError

logger = logging.getLogger(__name__)

Number = Union[int, float]
FactorOrFunc = Union[Number, Callable[[Number], Number]]


class UnitConverter:
    """Convert exact unit codes of a parameter addressed by its string ID.

    Unknown IDs raise UnknownParameterError and unknown unit codes raise
    UnknownUnitError. Names and UI labels are never used for lookup.
    Hardness conversion uses the bundled table and returns None outside valid intervals.
    """

    def __init__(self) -> None:
        self.parameters, self.hardness_data, self.presets = load_data()
        self._custom = {}
        self._hardness = HardnessConverter(self.hardness_data)

    def _get_parameter(self, type_id: str) -> Dict[str, Any]:
        if not isinstance(type_id, str) or type_id not in self.parameters:
            raise UnknownParameterError("Unknown parameter ID: {!r}".format(type_id))
        return self.parameters[type_id]

    def _check_unit(self, type_id: str, code: str) -> Dict[str, Any]:
        entry = self._get_parameter(type_id)
        if not isinstance(code, str) or code not in entry["factors"]:
            raise UnknownUnitError("Unknown unit {!r} for parameter {!r}".format(code, type_id))
        return entry

    def convert(self, value: Number, from_u: str, to_u: str, type_id: str) -> Optional[float]:
        """Convert through the base unit, without rounding registry factors."""
        entry = self._check_unit(type_id, from_u)
        self._check_unit(type_id, to_u)
        if from_u == to_u:
            return value
        if type_id not in ("1", "34") and (type_id, from_u) not in self._custom and (type_id, to_u) not in self._custom:
            return value * entry["factors"][from_u] / entry["factors"][to_u]
        base_value = self.to_base(value, from_u, type_id)
        if base_value is None:
            return None
        return self.from_base(base_value, to_u, type_id)

    def to_base(self, value: Number, from_u: str, type_id: str) -> Optional[float]:
        """Convert a registered unit code to its parameter's base unit."""
        entry = self._check_unit(type_id, from_u)
        custom = self._custom.get((type_id, from_u))
        if custom:
            return custom[0](value)
        if type_id == "34":
            return self._hardness.to_base(value, from_u)
        if type_id == "1":
            if from_u == "K":
                return value - const.CELSIUS_TO_KELVIN_OFFSET
            if from_u == "F":
                return (value - const.FAHRENHEIT_OFFSET) * const.FAHRENHEIT_RATIO
            if from_u == "Re":
                return value * const.REAUMUR_TO_CELSIUS
        factor = entry["factors"][from_u]
        return None if factor == const.TABLE else value * factor

    def from_base(self, value: Number, to_u: str, type_id: str) -> Optional[float]:
        """Convert the base value to a registered unit code."""
        entry = self._check_unit(type_id, to_u)
        custom = self._custom.get((type_id, to_u))
        if custom:
            return custom[1](value)
        if type_id == "34":
            return self._hardness.from_base(value, to_u)
        if type_id == "1":
            if to_u == "K":
                return value + const.CELSIUS_TO_KELVIN_OFFSET
            if to_u == "F":
                return value * const.FAHRENHEIT_RATIO_INV + const.FAHRENHEIT_OFFSET
            if to_u == "Re":
                return value * const.CELSIUS_TO_REAUMUR
        factor = entry["factors"][to_u]
        return None if factor == const.TABLE else value / factor

    def get_available_units(self, type_id: str) -> List[Dict[str, str]]:
        """Return code/UI pairs in registry order, as independent dictionaries."""
        entry = self._get_parameter(type_id)
        return [{"code": code, "ui": entry["display_labels"][code]} for code in entry["factors"]]

    def get_parameter_info(self, type_id: str) -> Dict[str, str]:
        """Return ID, Russian/English names and the base unit code."""
        entry = self._get_parameter(type_id)
        return dict(id=type_id, **{key: entry[key] for key in ("name_RU", "name_ENG", "base_unit")})

    def get_base_unit(self, type_id: str) -> str:
        """Return the exact base unit code."""
        return self._get_parameter(type_id)["base_unit"]

    def list_presets(self) -> List[str]:
        """Return preset names in data-file order."""
        return list(self.presets)

    def get_preset(self, name: str) -> Optional[Dict[str, str]]:
        """Return an independent raw ID/code mapping, or None for an unknown name."""
        preset = self.presets.get(name)
        return None if preset is None else copy.deepcopy(preset["units"])

    def apply_preset(self, name: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Resolve existing ID/code pairs to code/UI objects, logging omissions.

        This method does not convert values or alter the converter's registry.
        """
        units = self.get_preset(name)
        if units is None:
            return None
        result = {}
        for type_id, code in units.items():
            entry = self.parameters.get(type_id)
            if entry is None or code not in entry["factors"]:
                logger.warning("Preset %r: skipping invalid pair type_id=%r, code=%r", name, type_id, code)
                continue
            result[type_id] = {"code": code, "ui": entry["display_labels"][code]}
        return result

    def add_parameter(self, type_id: str, *, base_unit_symbol: str,
                      base_unit_name: str, parameter_name: str,
                      parameter_name_eng: Optional[str] = None) -> None:
        """Register a new decimal string ID in this instance only."""
        if not isinstance(type_id, str) or not type_id or not type_id.isascii() or not type_id.isdecimal():
            raise ValueError("type_id must be a decimal string ID")
        if type_id in self.parameters:
            raise ValueError("Parameter {!r} already exists".format(type_id))
        if not isinstance(base_unit_symbol, str) or not base_unit_symbol:
            raise ValueError("base_unit_symbol must be a nonempty code")
        self.parameters[type_id] = {
            "name_RU": parameter_name,
            "name_ENG": parameter_name_eng if parameter_name_eng is not None else parameter_name,
            "base_unit": base_unit_symbol,
            "factors": {base_unit_symbol: 1.0},
            "display_labels": {base_unit_symbol: base_unit_symbol},
        }

    def add_unit(self, type_id: str, *, unit_symbol: str, unit_name: str,
                 to_base: FactorOrFunc, from_base: Optional[FactorOrFunc] = None,
                 display_label: Optional[str] = None) -> None:
        """Add a factor or a pair of conversion functions to this instance.

        Callable to_base requires an explicit inverse. A numeric from_base is
        a multiplier, preserving the original dynamic extension convention.
        """
        entry = self._get_parameter(type_id)
        if not isinstance(unit_symbol, str) or not unit_symbol:
            raise ValueError("unit_symbol must be a nonempty code")
        if unit_symbol == entry["base_unit"]:
            raise ValueError("Cannot replace the base unit conversion")
        if callable(to_base):
            if from_base is None:
                raise ValueError("from_base is required for callable conversions")
            forward = to_base
        else:
            factor = float(to_base)
            if not math.isfinite(factor) or factor == 0:
                raise ValueError("to_base must be finite and nonzero")
            forward = lambda value: value * factor
        if from_base is None:
            inverse = lambda value: value / factor
        elif callable(from_base):
            inverse = from_base
        else:
            inverse_factor = float(from_base)
            if not math.isfinite(inverse_factor) or inverse_factor == 0:
                raise ValueError("from_base must be finite and nonzero")
            inverse = lambda value: value * inverse_factor
        entry["factors"][unit_symbol] = "custom" if callable(to_base) else factor
        entry["display_labels"][unit_symbol] = display_label if display_label is not None else unit_symbol
        self._custom[(type_id, unit_symbol)] = (forward, inverse)
