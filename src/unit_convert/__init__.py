"""unit_convert: convert across distance, weight, and heat scales.

Re-exports the ``convert`` function from ``unit_convert.core`` as the library's
single public entry point.
"""

from .core import convert, ConversionError, convert_temperature, convert_distance, convert_weight

__all__ = [
    "convert",
    "ConversionError",
    "convert_temperature",
    "convert_distance",
    "convert_weight",
]
