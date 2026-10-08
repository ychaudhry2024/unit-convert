"""Tests for unit_convert.core.

Conventions in this file:
- Temperature and weight assertions use ``math.isclose`` because the results
  are floats that may carry rounding noise from the conversion factors.
- Where a result is expected to be exact (same-unit round trips, or integer
  metric-to-metric steps), we still use ``isclose`` with a tight relative
  tolerance rather than ``==`` — this is the convention the README promises
  callers, and tests should model the contract callers will actually rely on.
"""

import math
import unittest

from unit_convert import core
from unit_convert import (
    convert,
    ConversionError,
    convert_temperature,
    convert_distance,
    convert_weight,
)


class TestDistance(unittest.TestCase):
    def test_meters_to_cm(self):
        self.assertTrue(math.isclose(convert(1, "m", "cm"), 100.0, rel_tol=1e-12))

    def test_km_to_miles(self):
        # 1 km = 1000 m; 1 mile = 1609.344 m exactly (by international agreement).
        self.assertTrue(math.isclose(convert(1, "km", "mi"), 1000.0 / 1609.344, rel_tol=1e-12))

    def test_inches_to_mm(self):
        self.assertTrue(math.isclose(convert(1, "in", "mm"), 25.4, rel_tol=1e-12))

    def test_same_unit_returns_input_as_float(self):
        result = convert(5, "m", "m")
        self.assertEqual(result, 5.0)
        self.assertIsInstance(result, float)

    def test_case_and_whitespace_insensitive(self):
        self.assertTrue(math.isclose(convert(1, "  M ", "Cm"), 100.0, rel_tol=1e-12))

    def test_integer_input_promoted_to_float(self):
        result = convert(2, "m", "cm")
        self.assertIsInstance(result, float)
        self.assertTrue(math.isclose(result, 200.0, rel_tol=1e-12))

    def test_unknown_from_unit_raises(self):
        with self.assertRaises(ConversionError):
            convert(1, "smoot", "m")

    def test_unknown_to_unit_raises(self):
        with self.assertRaises(ConversionError):
            convert(1, "m", "parsec")


class TestWeight(unittest.TestCase):
    def test_kg_to_g(self):
        self.assertTrue(math.isclose(convert(1, "kg", "g"), 1000.0, rel_tol=1e-12))

    def test_lb_to_oz(self):
        # 1 lb = 453.59237 g; 1 oz = 28.349523125 g.
        expected = 453.59237 / 28.349523125
        self.assertTrue(math.isclose(convert(1, "lb", "oz"), expected, rel_tol=1e-12))

    def test_round_trip_lb_to_kg_to_lb(self):
        original = 7.0
        round_tripped = convert(convert(original, "lb", "kg"), "kg", "lb")
        self.assertTrue(math.isclose(round_tripped, original, rel_tol=1e-12))

    def test_mg_to_kg(self):
        self.assertTrue(math.isclose(convert(1_000_000, "mg", "kg"), 1.0, rel_tol=1e-12))


class TestTemperature(unittest.TestCase):
    def test_c_to_f_freezing(self):
        self.assertTrue(math.isclose(convert(0, "c", "f"), 32.0, rel_tol=1e-12))

    def test_c_to_f_boiling(self):
        self.assertTrue(math.isclose(convert(100, "c", "f"), 212.0, rel_tol=1e-12))

    def test_f_to_c_body_temperature(self):
        self.assertTrue(math.isclose(convert(98.6, "f", "c"), 37.0, rel_tol=1e-9, abs_tol=1e-9))

    def test_c_to_k_absolute_zero(self):
        self.assertTrue(math.isclose(convert(-273.15, "c", "k"), 0.0, abs_tol=1e-9))

    def test_k_to_c_round_trip(self):
        original = 300.0
        round_tripped = convert(convert(original, "k", "f"), "f", "k")
        self.assertTrue(math.isclose(round_tripped, original, rel_tol=1e-9))

    def test_f_to_k_directly(self):
        # 32 F = 0 C = 273.15 K
        self.assertTrue(math.isclose(convert(32, "f", "k"), 273.15, rel_tol=1e-9))

    def test_kelvin_negative_input_allowed(self):
        # The library does not police physical meaningfulness; it only converts.
        # A negative Kelvin reading is the caller's problem, not ours.
        self.assertTrue(math.isclose(convert(-10, "k", "c"), -283.15, rel_tol=1e-9))


class TestDispatchAndValidation(unittest.TestCase):
    def test_cross_family_conversion_rejected(self):
        with self.assertRaises(ConversionError):
            convert(1, "m", "kg")

    def test_cross_family_temperature_to_distance_rejected(self):
        with self.assertRaises(ConversionError):
            convert(1, "c", "m")

    def test_bool_value_rejected(self):
        # bool is a subclass of int but is not a measurement.
        with self.assertRaises(ConversionError):
            convert(True, "m", "cm")

    def test_non_numeric_value_rejected(self):
        with self.assertRaises(ConversionError):
            convert("five", "m", "cm")

    def test_non_string_unit_rejected(self):
        with self.assertRaises(ConversionError):
            convert(1, 5, "cm")

    def test_conversion_error_is_value_error(self):
        # Callers catching ValueError should also catch ConversionError.
        try:
            convert(1, "m", "smoot")
        except ValueError:
            pass
        else:
            self.fail("ConversionError did not propagate as ValueError")

    def test_explicit_temperature_function_matches_general(self):
        a = convert_temperature(100, "c", "f")
        b = convert(100, "c", "f")
        self.assertTrue(math.isclose(a, b, rel_tol=1e-12))

    def test_explicit_distance_function_matches_general(self):
        a = convert_distance(1, "mi", "m")
        b = convert(1, "mi", "m")
        self.assertTrue(math.isclose(a, b, rel_tol=1e-12))

    def test_explicit_weight_function_matches_general(self):
        a = convert_weight(1, "kg", "lb")
        b = convert(1, "kg", "lb")
        self.assertTrue(math.isclose(a, b, rel_tol=1e-12))

    def test_explicit_temperature_rejects_distance_unit(self):
        with self.assertRaises(ConversionError):
            convert_temperature(1, "c", "m")

    def test_explicit_distance_rejects_weight_unit(self):
        with self.assertRaises(ConversionError):
            convert_distance(1, "m", "kg")


if __name__ == "__main__":
    unittest.main()
