from __future__ import annotations

__all__ = [
    "convert",
    "ConversionError",
    "convert_temperature",
    "convert_distance",
    "convert_weight",
]


class ConversionError(ValueError):
    """Raised when a unit is unknown or a conversion is unsupported.

    Subclassing ``ValueError`` keeps it catchable by callers who only know
    ``ValueError`` — useful when the library is used as one validation step
    among several in a data pipeline.
    """


# Distance — base unit meters. Linear, so the round-trip is exact in floats
# up to rounding noise, which tests tolerate via ``math.isclose``.
_DISTANCE_FACTORS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344,
}

# Weight — base unit grams. Same linear reasoning as distance.
_WEIGHT_FACTORS = {
    "mg": 0.001,
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.349523125,
    "lb": 453.59237,
}


def _convert_linear(value, from_unit, to_unit, factors, kind):
    """Shared path for multiplicative unit sets (distance, weight).

    "value" must already be a float when it reaches here; the caller is
    responsible for coercion so that this function has exactly one job.
    "kind" is only used to build a helpful error string.
    """
    if from_unit not in factors:
        raise ConversionError(f"unknown {kind} unit: {from_unit!r}")
    if to_unit not in factors:
        raise ConversionError(f"unknown {kind} unit: {to_unit!r}")
    base = value * factors[from_unit]
    return base / factors[to_unit]


def _celsius_to_fahrenheit(c):
    """Celsius → Fahrenheit. Offset 32 matters, hence no factor table."""
    return c * 9.0 / 5.0 + 32.0


def _fahrenheit_to_celsius(f):
    """Fahrenheit → Celsius. Inverse of the above; kept explicit for clarity."""
    return (f - 32.0) * 5.0 / 9.0


def _celsius_to_kelvin(c):
    """Celsius → Kelvin. Same scale, different origin."""
    return c + 273.15


def _kelvin_to_celsius(k):
    """Kelvin → Celsius."""
    return k - 273.15


def _to_celsius(value, unit):
    """Route any temperature unit to Celsius as the shared base."""
    if unit == "c":
        return value
    if unit == "f":
        return _fahrenheit_to_celsius(value)
    if unit == "k":
        return _kelvin_to_celsius(value)
    raise ConversionError(f"unknown temperature unit: {unit!r}")


def _from_celsius(celsius, unit):
    """Route Celsius out to the requested temperature unit."""
    if unit == "c":
        return celsius
    if unit == "f":
        return _celsius_to_fahrenheit(celsius)
    if unit == "k":
        return _celsius_to_kelvin(celsius)
    raise ConversionError(f"unknown temperature unit: {unit!r}")


_TEMPERATURE_UNITS = {"c", "f", "k"}
_DISTANCE_UNITS = set(_DISTANCE_FACTORS)
_WEIGHT_UNITS = set(_WEIGHT_FACTORS)


def _coerce_number(value, kind):
    """Accept int/float and reject everything else, early.

    ``bool`` is a subclass of ``int`` in Python; we explicitly exclude it because
    "convert True to meters" is a bug in the caller, not a measurement.
    """
    if isinstance(value, bool):
        raise ConversionError(f"{kind} value must be a number, not bool")
    if isinstance(value, (int, float)):
        return float(value)
    raise ConversionError(f"{kind} value must be a number, got {type(value).__name__}")


def _coerce_unit(unit):
    """Units are matched case-insensitively and with whitespace trimmed.

    Users type units from forms and CLI arguments; ' kg ' and 'KG' should both
    work. We do not accept Unicode prefixes (e.g. the µ in 'µg') because that
    opens the door to normalization ambiguities we do not want to own.
    """
    if not isinstance(unit, str):
        raise ConversionError(f"unit must be a string, got {type(unit).__name__}")
    return unit.strip().lower()


def _detect_kind(from_unit, to_unit):
    """Figure out which unit family a pair belongs to.

    Both units must be in the same family. Cross-family conversion (e.g.
    'meters to kilograms') is rejected because it has no physically meaningful
    answer, and silently returning 0 or NaN would be worse than failing loud.
    """
    from_u = _coerce_unit(from_unit)
    to_u = _coerce_unit(to_unit)
    if from_u in _TEMPERATURE_UNITS and to_u in _TEMPERATURE_UNITS:
        return "temperature", from_u, to_u
    if from_u in _DISTANCE_UNITS and to_u in _DISTANCE_UNITS:
        return "distance", from_u, to_u
    if from_u in _WEIGHT_UNITS and to_u in _WEIGHT_UNITS:
        return "weight", from_u, to_u
    # If from and to are each known but in different families, say so plainly.
    known = _TEMPERATURE_UNITS | _DISTANCE_UNITS | _WEIGHT_UNITS
    if from_u in known and to_u in known:
        raise ConversionError(
            f"cannot convert between unrelated units: {from_u!r} and {to_u!r}"
        )
    # Otherwise at least one is unknown — name the first offender we spot.
    if from_u not in known:
        raise ConversionError(f"unknown unit: {from_u!r}")
    raise ConversionError(f"unknown unit: {to_u!r}")


def convert_temperature(value, from_unit, to_unit):
    """Convert a temperature value between ``c``, ``f``, and ``k``."""
    v = _coerce_number(value, "temperature")
    fu = _coerce_unit(from_unit)
    tu = _coerce_unit(to_unit)
    if fu not in _TEMPERATURE_UNITS:
        raise ConversionError(f"unknown temperature unit: {fu!r}")
    if tu not in _TEMPERATURE_UNITS:
        raise ConversionError(f"unknown temperature unit: {tu!r}")
    return _from_celsius(_to_celsius(v, fu), tu)


def convert_distance(value, from_unit, to_unit):
    """Convert a distance between mm, cm, m, km, in, ft, yd, mi."""
    v = _coerce_number(value, "distance")
    fu = _coerce_unit(from_unit)
    tu = _coerce_unit(to_unit)
    return _convert_linear(v, fu, tu, _DISTANCE_FACTORS, "distance")


def convert_weight(value, from_unit, to_unit):
    """Convert a weight between mg, g, kg, oz, lb."""
    v = _coerce_number(value, "weight")
    fu = _coerce_unit(from_unit)
    tu = _coerce_unit(to_unit)
    return _convert_linear(v, fu, tu, _WEIGHT_FACTORS, "weight")


def convert(value, from_unit, to_unit):
    """Convert ``value`` from ``from_unit`` to ``to_unit``.

    Dispatches on the unit family (distance / weight / temperature) and returns
    a float. Raises ``ConversionError`` if the units are unknown or if they
    belong to different families (e.g. meters → kilograms).

    Units are matched case-insensitively and with surrounding whitespace
    trimmed, so ``convert(1, ' M ', 'cm')`` works.
    """
    kind, fu, tu = _detect_kind(from_unit, to_unit)
    if kind == "temperature":
        return convert_temperature(value, fu, tu)
    if kind == "distance":
        return convert_distance(value, fu, tu)
    return convert_weight(value, fu, tu)
