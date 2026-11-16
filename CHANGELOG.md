# Changelog

## 2.0.0 — 2026-11-03

### Breaking changes

- Parameter lookup uses exact string IDs ("0" through "47") instead of names.
- `convert(value, from_u, to_u, type_id)` accepts positional or keyword arguments.
  Legacy `parameter_type`, `from_unit` and `to_unit` keywords are removed.
- Unit lookup uses registry codes, for example `кгс/см2`; UI labels such as
  `кгс/см²` are for display only.
- `get_available_units(type_id)` returns a list of `{code, ui}` dictionaries.
- `parameters` now contains the external registry structure, including `factors`
  and `display_labels`, rather than the legacy callable-based unit dictionary.
- Unknown IDs consistently raise `UnknownParameterError`; unknown unit codes
  raise `UnknownUnitError`.

### Added

- External registry of 48 engineering quantities, included in wheel and sdist.
- `get_parameter_info(type_id)` and helpers for conversion to/from base units.
- Temperature conversion between C, K, F and Re through Celsius.
- Seven hardness scales with interpolation through HB and no extrapolation.
- SI, TECH and IMPERIAL presets with validation, UI labels and warning logs.
- Named constants and safe, initialization-time resolution of `@NAME` references
  and arithmetic expressions in registry factors.
- Diagnosable `DataLoadError` for missing, corrupt or invalid package resources.
- Instance-local extension through `add_parameter` and `add_unit` using IDs.
- Updated documentation and 35 tests covering conversion, loading and examples.

### Numerical behavior and limitations

- Standard conversion factors now use precise defining constants instead of
  rounded values from the original registry appendix.
- Hardness gaps break interpolation intervals. Repeated source values use the
  first valid table row; tabulated conversions need not be exactly reversible.
- Preset source data retains invalid pairs from the specification (SI: 2,
  TECH: 1, IMPERIAL: 10). `apply_preset` omits them with warnings.
- Physical validity of input values, such as temperatures below absolute zero,
  is not enforced by the conversion API.

### Migration example

```python
from uniconv import UnitConverter

uc = UnitConverter()
# Version 1.x:
# uc.convert(10, from_unit="бар", to_unit="МПа", parameter_type="pressure")
# Version 2.x:
value = uc.convert(10, from_u="бар", to_u="МПа", type_id="0")
assert value == 1.0
```
