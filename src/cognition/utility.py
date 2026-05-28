"""
Utility code
"""

from typing import (
    Any,
    Optional,
    Protocol,
)

from collections.abc import (
    Callable,
    Mapping,
)

from functools import wraps

#

class AttrReferral:
    """
    Read-only .key access to a value via external mapping { key:value }
    """

    # private field name for the mapping reference
    _ref_field_name: str = '_attr_mapping'

    #

    def __init__(self, external_source: Mapping[str, Any]) -> None:
        """
        :param external_source: mapping reference
        """

        object.__setattr__(
            self,
            AttrReferral._ref_field_name,
            external_source
        )

    def __getattr__(self, key: str) -> Any:
        if key not in self.__getattribute__(AttrReferral._ref_field_name):
            raise AttributeError(f"Contains no such key: '{key}'")

        return self.__getattribute__(AttrReferral._ref_field_name)[key]

    def __setattr__(self, _key: str, _value: Any) -> None:
        """
        :raises AttributeError: read-only access
        """

        raise AttributeError(f"'{type(self).__name__}' object attributes are read-only.")


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


def optionally_name[**P, R](f: Callable[P, R], name: Optional[str]) -> Callable[P, R]:
    """
    Shorthand for optionally providing a callable an ``str()`` value

    :param f: callable to optionally augment
    :param name: value to return upon ``str()``, if supplied
    :return: stringify'd function if a name is supplied; otherwise the original function
    """

    if name:
        return stringify(name)(f)

    return f
