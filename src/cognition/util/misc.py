"""
Misc utility code
"""

from __future__ import annotations

import time
from collections.abc import (
    Callable,
    Mapping,
)
from functools import wraps
from types import MappingProxyType
from typing import (
    Any,
    Protocol,
    cast,
)

# ===


# pylint: disable=too-few-public-methods
class MutableWrapper[T]:
    """
    Supports in-place modification
    of (potentially) immutable types
    given a shared reference
    """

    value: T

    def __init__(self, value: T) -> None:
        """
        :param value: initial value
        """

        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"MutableWrapper({self.value!r})"


class AttrReferral:
    """
    Read-only .key access to a value via external mapping { key:value }
    """

    # private field name for the mapping reference
    _ref_field_name: str = "_attr_mapping"

    # private field name for the mapping view
    _view_field_name: str = "_mapping_view"

    # ===

    @staticmethod
    def view(obj: AttrReferral) -> MappingProxyType[str, Any]:
        """
        :param obj: object of interest
        :return: read-only mapping of available key/value pairs
        """

        # pylint: disable=unnecessary-dunder-call
        return cast(
            MappingProxyType[str, Any],
            obj.__getattribute__(AttrReferral._view_field_name),
        )

    # ===

    def __init__(self, external_source: Mapping[str, Any]) -> None:
        """
        :param external_source: mapping reference
        """

        object.__setattr__(self, AttrReferral._ref_field_name, external_source)
        object.__setattr__(
            self, AttrReferral._view_field_name, MappingProxyType(external_source)
        )

    def __getattr__(self, key: str) -> Any:
        if key not in self.__getattribute__(AttrReferral._ref_field_name):
            raise AttributeError(f"Contains no such key: '{key}'")

        return self.__getattribute__(AttrReferral._ref_field_name)[key]

    def __setattr__(self, _key: str, _value: Any) -> None:
        """
        :raises AttributeError: read-only access
        """

        raise AttributeError(
            f"'{type(self).__name__}' object attributes are read-only."
        )


# pylint: disable=too-few-public-methods
class ImplementsLessThan(Protocol):
    """
    A type with ``<`` implementation (useful for sorting)
    """

    def __lt__(self, other: Any) -> bool: ...


class StringifiedFunction[**P, R]:
    """
    A callable object that wraps a function and provides a custom ``str()`` value.
    """

    def __init__(self, func: Callable[P, R], str_value: str):
        """
        :param func: wrapped function
        :param str_value: to supply upon ``str(self)``
        """

        wraps(func)(self)
        self._func: Callable[P, R] = func
        self._str_value: str = str_value

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Calls the wrapped function
        """

        return self._func(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns the custom string value
        """

        return self._str_value


# pylint: disable=invalid-name
def stringify[**P, R](str_value: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for providing a callable with an ``str()`` value

    :param str_value: value to return upon ``str()``
    :return: resulting callable
    """

    def decorated(func: Callable[P, R]) -> Callable[P, R]:
        """
        Newly wrapped function

        :param func: original function
        :return: resulting callable
        """

        return StringifiedFunction(func, str_value)

    return decorated


def optionally_name[**P, R](f: Callable[P, R], name: str | None) -> Callable[P, R]:
    """
    Shorthand for optionally providing a callable an ``str()`` value

    :param f: callable to optionally augment
    :param name: value to return upon ``str()``, if supplied
    :return: stringify'd function if a name is supplied; otherwise the original function
    """

    if name:
        return stringify(name)(f)

    return f


def timed[**P, R](f: Callable[P, R]) -> Callable[P, tuple[R, float]]:
    """
    Decorator to time the execution of the supplied function

    :param f: function to decorate
    :return: function that times each invocation
    """

    @wraps(f)
    def _wrapped(*args: P.args, **kwargs: P.kwargs) -> tuple[R, float]:
        start_t = time.perf_counter()
        result = f(*args, **kwargs)
        end_t = time.perf_counter()

        return (result, end_t - start_t)

    return _wrapped
