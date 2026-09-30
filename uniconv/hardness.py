"""Piecewise linear hardness conversion through HB, without extrapolation."""

from bisect import bisect_left
import math

from .constants import HARDNESS_SCALES


class HardnessConverter:
    """Cache both directions of each scale's contiguous valid table segments.

    Missing cells break an interval. Repeated source values select the first
    valid row in the source table, so rounded HB values have deterministic results.
    """

    def __init__(self, rows):
        self._segments = {}
        hb_column = HARDNESS_SCALES.index("HB")
        for column, scale in enumerate(HARDNESS_SCALES):
            if scale == "HB":
                continue
            segments, current = [], []
            for row in rows:
                if row[column] is None or row[hb_column] is None:
                    if current:
                        segments.append(current)
                        current = []
                else:
                    current.append((row[hb_column], row[column]))
            if current:
                segments.append(current)
            for reverse in (False, True):
                prepared = []
                for segment in segments:
                    pairs = [(b, a) for a, b in segment] if reverse else segment
                    # Stable sort preserves the first table row for duplicate values.
                    pairs = sorted(pairs, key=lambda pair: pair[0])
                    unique = []
                    for pair in pairs:
                        if not unique or unique[-1][0] != pair[0]:
                            unique.append(pair)
                    prepared.append(([pair[0] for pair in unique], [pair[1] for pair in unique]))
                self._segments[(scale, reverse)] = prepared

    def _interpolate(self, value, scale, reverse):
        if not math.isfinite(value):
            return None
        for xs, ys in self._segments.get((scale, reverse), []):
            index = bisect_left(xs, value)
            if index < len(xs) and xs[index] == value:
                return ys[index]
            if 0 < index < len(xs):
                left = index - 1
                return ys[left] + (value - xs[left]) * (ys[index] - ys[left]) / (xs[index] - xs[left])
        return None

    def to_base(self, value, scale):
        return value if scale == "HB" else self._interpolate(value, scale, True)

    def from_base(self, value, scale):
        return value if scale == "HB" else self._interpolate(value, scale, False)
