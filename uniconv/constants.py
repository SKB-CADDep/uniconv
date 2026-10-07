"""Named conversion constants (BR-06/BR-08); all conversion factors use SI anchors.

Unit and provenance are documented with each assignment. Engineering reference
values without an authoritative exact definition retain the supplied registry value.
"""

import math

PI = math.pi
"""Dimensionless pi; Python math.pi."""
E = math.e
"""Dimensionless Euler number; Python math.e."""
TWO_PI = 2 * PI
"""Radians per complete revolution."""
DEG_TO_RAD = PI / 180
"""Radians per degree; full circle is 360 degrees."""
RAD_TO_DEG = 180 / PI
"""Degrees per radian."""
G_STANDARD = 9.80665
"""Standard gravity, m/s²; CGPM 1901, conventional exact value."""
STANDARD_ATMOSPHERE = 101325.0
"""Standard atmosphere, Pa; BIPM SI Brochure."""
RHO_H2O_4C = 1000.0
"""Conventional water density at 4 °C, kg/m³; supplied specification."""
RHO_HG_0C = 13595.1
"""Reference mercury density at 0 °C, kg/m³; supplied specification."""
INCH_TO_MM = 25.4
"""International inch, mm; international yard and pound agreement, 1959."""
FOOT_TO_MM = 304.8
"""International foot, mm; international yard and pound agreement, 1959."""
YARD_TO_MM = 914.4
"""International yard, mm; international yard and pound agreement, 1959."""
MILE_TO_MM = 1609344.0
"""International statute mile, mm; international yard and pound agreement."""
LB_TO_KG = 0.45359237
"""International avoirdupois pound, kg; international agreement, 1959."""
CAL_TO_J = 4.1868
"""International Table calorie, J; supplied specification (IT calorie)."""
LIGHT_YEAR_TO_MM = 9.4607e18
"""Reference light year, mm; value prescribed by Appendix 4."""
MINUTE_TO_S = 60.0
"""Minute, s; SI Brochure, non-SI units accepted for use with SI."""
HOUR_TO_S = 3600.0
"""Hour, s; SI Brochure, non-SI units accepted for use with SI."""
DAY_TO_S = 86400.0
"""Day, s; SI Brochure, non-SI units accepted for use with SI."""
YEAR_365D_TO_S = 31536000.0
"""Conventional 365-day year, s; supplied specification."""
CELSIUS_TO_KELVIN_OFFSET = 273.15
"""Celsius/Kelvin origin offset, K; SI Brochure."""
FAHRENHEIT_OFFSET = 32.0
"""Fahrenheit freezing-point offset, °F; supplied specification."""
FAHRENHEIT_RATIO = 5 / 9
"""Celsius degrees per Fahrenheit degree; supplied specification."""
FAHRENHEIT_RATIO_INV = 9 / 5
"""Fahrenheit degrees per Celsius degree; supplied specification."""
REAUMUR_TO_CELSIUS = 1.25
"""Celsius degrees per Reaumur degree; supplied specification."""
CELSIUS_TO_REAUMUR = 0.8
"""Reaumur degrees per Celsius degree; supplied specification."""
KGF_TO_N = G_STANDARD
"""Kilogram-force, N; derived from standard gravity."""
LBF_TO_N = LB_TO_KG * G_STANDARD
"""Pound-force, N; derived from the international pound and standard gravity."""
HP_METRIC_TO_W = 75 * G_STANDARD
"""Metric horsepower, W; 75 kgf·m/s by definition."""
MMHG_TO_PA = 133.322387415
"""Conventional millimetre of mercury, Pa; value prescribed by Appendix 4."""
MMH2O_TO_PA = RHO_H2O_4C * G_STANDARD / 1000
"""Millimetre water column, Pa; derived from conventional water density."""
PERCENT = 0.01
"""Dimensionless fraction per percent."""
KGF_PER_CM2_TO_PA = G_STANDARD * 1e4
"""Technical atmosphere, Pa; compatibility name, derived from gravity."""
ATM_TO_PA = STANDARD_ATMOSPHERE
"""Standard atmosphere, Pa; compatibility name."""
BAR_TO_PA = 1e5
"""Bar, Pa; SI Brochure, exact scale factor."""
MM_HG_TO_PA = MMHG_TO_PA
"""Millimetre of mercury, Pa; compatibility name."""
HP_TO_W = HP_METRIC_TO_W
"""Metric horsepower, W; compatibility name."""
T_PER_H_TO_KG_PER_S = 1000 / HOUR_TO_S
"""Tonne per hour, kg/s; derived from SI mass and time scales."""
NAUTICAL_MILE_TO_M = 1852.0
"""International nautical mile, m; conventional exact definition."""
SHORT_TON_TO_LB = 2000.0
"""US short ton, lb; conventional definition used by tsf."""
VERSHOK_TO_MM = 44.45
"""Vershok, mm; supplied registry reference value."""
PYAD_TO_MM = 177.8
"""Pyad, mm; supplied registry reference value."""
ARSHIN_TO_MM = 711.2
"""Arshin, mm; supplied registry reference value."""
SAZHEN_TO_MM = 2133.6
"""Sazhen, mm; supplied registry reference value."""
VERST_TO_MM = 1066800.0
"""Verst, mm; supplied registry reference value."""
LEAGUE_TO_MM = 5556000.0
"""League, mm; supplied registry reference value."""
ACRE_TO_M2 = 4046.86
"""Acre, m²; supplied registry reference precision."""
BARREL_TO_M3 = 0.158987
"""US oil barrel, m³; supplied registry reference precision."""
GALLON_US_TO_M3 = 0.00378541
"""US liquid gallon, m³; supplied registry reference precision."""
OUNCE_TO_KG = 0.02835
"""Avoirdupois ounce, kg; supplied registry reference precision."""
DB_TO_NP = 0.1151
"""Amplitude decibel, Np; supplied registry reference precision."""
TABLE = "table"
"""Registry marker for hardness lookup."""
OFFSET_K = "offset_k"
"""Registry marker for Kelvin temperature conversion."""
OFFSET_F = "offset_f"
"""Registry marker for Fahrenheit temperature conversion."""
OFFSET_RE = "offset_re"
"""Registry marker for Reaumur temperature conversion."""
HARDNESS_SCALES = ("d10", "HB", "HRA", "HRC", "HRB", "HV", "HSD")
"""Column order in the hardness table."""
