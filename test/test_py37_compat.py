import math as stdlib_math
import unittest

from yt_dlp._compat_py37 import _CachedProperty, _nextafter, _ulp, compat_zip


class TestPython37Compatibility(unittest.TestCase):
    def test_strict_zip_equal_lengths(self) -> None:
        self.assertEqual(list(compat_zip([1, 2], ['a', 'b'], strict=True)), [(1, 'a'), (2, 'b')])
        self.assertEqual(list(compat_zip(strict=True)), [])

    def test_strict_zip_different_lengths(self) -> None:
        for left, right in [([], [1]), ([1], []), ([1, 2], [3]), ([1], [2, 3])]:
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    list(compat_zip(left, right, strict=True))

    def test_ulp_zero_and_subnormal(self) -> None:
        minimum = float.fromhex('0x0.0000000000001p-1022')
        self.assertEqual(_ulp(0.0), minimum)
        self.assertEqual(_ulp(minimum), minimum)
        self.assertEqual(_ulp(1.0), 2**-52)

    def test_nextafter_signed_zero(self) -> None:
        minimum = float.fromhex('0x0.0000000000001p-1022')
        self.assertEqual(_nextafter(0.0, 1.0), minimum)
        self.assertEqual(_nextafter(0.0, -1.0), -minimum)
        self.assertEqual(stdlib_math.copysign(1.0, _nextafter(0.0, -0.0)), -1.0)

    def test_nextafter_and_ulp_match_modern_python(self) -> None:
        if not hasattr(stdlib_math, 'nextafter'):
            self.skipTest('Reference implementations require Python 3.9')
        for value in [-float('inf'), -1e308, -1.0, -1e-320, 0.0, 1e-320, 1.0, 1e308, float('inf')]:
            with self.subTest(value=value):
                self.assertEqual(_ulp(value), stdlib_math.ulp(value))
                for towards in [-float('inf'), -1.0, 0.0, 1.0, float('inf')]:
                    self.assertEqual(_nextafter(value, towards), stdlib_math.nextafter(value, towards))

    def test_cached_property_caches_each_instance(self) -> None:
        class Example:
            calls = 0

            @_CachedProperty
            def value(self) -> int:
                self.calls += 1
                return self.calls

        first, second = Example(), Example()
        self.assertEqual((first.value, first.value, second.value), (1, 1, 1))
        del first.value
        self.assertEqual(first.value, 2)
