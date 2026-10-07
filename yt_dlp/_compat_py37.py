"""Standard-library compatibility for the Python 3.7 fork."""

from __future__ import annotations

import builtins
import functools as _functools
import itertools as _itertools
import math as _math
import shlex as _shlex
import struct
import types
from typing import Any, Callable, Iterable, Iterator, Optional, Tuple


class _CachedProperty:
    def __init__(self, func: Callable[..., Any]) -> None:
        _functools.update_wrapper(self, func)
        self.func = func

    def __get__(self, instance: Optional[object], owner: type) -> Any:
        if instance is None:
            return self
        result = self.func(instance)
        instance.__dict__[self.func.__name__] = result
        return result


def _module_copy(original: types.ModuleType) -> types.ModuleType:
    module = types.ModuleType(original.__name__)
    module.__dict__.update(vars(original))
    return module


functools = _module_copy(_functools)
if not hasattr(functools, 'cache'):
    functools.cache = _functools.lru_cache(maxsize=None)
if not hasattr(functools, 'cached_property'):
    functools.cached_property = _CachedProperty


def _shlex_join(arguments: Iterable[str]) -> str:
    return ' '.join(_shlex.quote(argument) for argument in arguments)


shlex = _module_copy(_shlex)
if not hasattr(shlex, 'join'):
    shlex.join = _shlex_join


def _pairwise(iterable: Iterable[Any]) -> Iterator[Tuple[Any, Any]]:
    first, second = _itertools.tee(iterable)
    next(second, None)
    return builtins.zip(first, second)


itertools = _module_copy(_itertools)
if not hasattr(itertools, 'pairwise'):
    itertools.pairwise = _pairwise


def _nextafter(value: float, towards: float) -> float:
    if _math.isnan(value) or _math.isnan(towards):
        return value + towards
    if value == towards:
        return towards
    if value == 0:
        return _math.copysign(float.fromhex('0x0.0000000000001p-1022'), towards)
    bits = struct.unpack('>Q', struct.pack('>d', value))[0]
    bits += 1 if (value > 0) == (towards > value) else -1
    return struct.unpack('>d', struct.pack('>Q', bits))[0]


def _ulp(value: float) -> float:
    value = abs(value)
    if not _math.isfinite(value):
        return value
    if value == 0:
        return float.fromhex('0x0.0000000000001p-1022')
    exponent = _math.frexp(value)[1]
    return _math.ldexp(1.0, max(exponent - 53, -1074))


math = _module_copy(_math)
if not hasattr(math, 'nextafter'):
    math.nextafter = _nextafter
if not hasattr(math, 'ulp'):
    math.ulp = _ulp

NoneType = type(None)


def _strict_zip(iterators: Tuple[Iterator[Any], ...]) -> Iterator[Tuple[Any, ...]]:
    while iterators:
        row = []
        for index, iterator in enumerate(iterators):
            try:
                row.append(next(iterator))
            except StopIteration:
                if row:
                    raise ValueError('zip() arguments have different lengths')
                sentinel = object()
                if any(next(remaining, sentinel) is not sentinel for remaining in iterators[index + 1 :]):
                    raise ValueError('zip() arguments have different lengths')
                return
        yield tuple(row)


def compat_zip(*iterables: Iterable[Any], strict: bool = False) -> Iterator[Tuple[Any, ...]]:
    if not strict:
        return builtins.zip(*iterables)
    return _strict_zip(tuple(iter(iterable) for iterable in iterables))
