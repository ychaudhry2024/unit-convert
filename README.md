# unit_convert

Convert measurements across distance, weight, and temperature scales. Standard library only, no dependencies.

## Usage

```python
from unit_convert import convert, ConversionError

convert(1, "m", "cm")        # 100.0
convert(100, "c", "f")       # 212.0
convert(1, "kg", "lb")        # 2.2046226218487757

try:
    convert(1, "m", "kg")
except ConversionError as e:
    print(e)  # cannot convert between unrelated units: 'm' and 'kg'
```

Specialized entry points exist for each family and accept the same units:

```python
from unit_convert import convert_distance, convert_weight, convert_temperature

convert_distance(1, "mi", "m")      # 1609.344
convert_weight(1, "oz", "g")         # 28.349523125
convert_temperature(0, "c", "k")     # 273.15
```

Supported units:

- **Distance:** `mm`, `cm`, `m`, `km`, `in`, `ft`, `yd`, `mi`
- **Weight:** `mg`, `g`, `kg`, `oz`, `lb`
- **Temperature:** `c` (Celsius), `f` (Fahrenheit), `k` (Kelvin)

Units are matched case-insensitively and with surrounding whitespace trimmed, so `convert(1, " M ", "CM")` works.

All numeric results are returned as `float`.

## Why this exists

The recurring problem when converting units in small scripts is that temperature is not multiplicatively scalable — Fahrenheit and Celsius disagree on where zero is — so a single factor table cannot cover both temperature and distance/weight. This library gives each unit an explicit `to_base`/`from_base` path so the temperature offset is visible in code rather than hidden inside a formula that also has to handle linear units.

The trade-off: the unit set is fixed and small. If you need a unit that is not listed above, this library will not help you. Adding a unit means editing `core.py`; there is no plugin or registration mechanism, because that machinery would be larger than the conversion logic itself.

## Edge cases you will hit

- **Cross-family conversion is rejected.** `convert(1, "m", "kg")` raises `ConversionError`. There is no physically meaningful answer, and returning zero or NaN would be worse than failing.
- **`bool` is rejected as a value.** `convert(True, "m", "cm")` raises `ConversionError`, even though `bool` is a subclass of `int` in Python. Passing `True` as a measurement is a caller bug.
- **Floats are compared with tolerance, not `==`.** The conversion factors for `lb`, `oz`, and `mi` are not integers; round-trips accumulate rounding noise. Compare results with `math.isclose`, not equality.
- **Negative Kelvin is allowed.** The library does not police physical meaningfulness. A negative Kelvin reading is the caller's concern; the conversion is still mathematically defined.

`ConversionError` subclasses `ValueError`, so code that catches `ValueError` will also catch it.
