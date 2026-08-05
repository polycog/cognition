"""
Enumeration support
"""

from enum import Enum
from typing import Any, Self

# ===


class DocEnum(Enum):
    """
    An enumeration where members can have individual docstrings.

    Example usage::

        MEMBER = value[, "docstring"]
    """

    def __new__(cls, *args: Any) -> Self:
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, *args: Any) -> None:
        if len(args) == 2 and isinstance(args[-1], str):
            self.__doc__ = args[-1]
        else:
            self.__doc__ = None


class AutoDocEnum(Enum):
    """
    An enumeration where members have individual docstrings
    and the value is automatically set (as integers: 1, 2, ...)

    Example usage::
    
        MEMBER = "docstring"
    """

    def __new__(cls, *args: Any) -> Self:
        value = len(cls) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, *args: Any) -> None:
        self.__doc__ = str(args[0])


# pylint: disable=too-few-public-methods
class EnumDispatch[T: Enum]:
    """
    Support for dispatch to an object's
    methods based upon supplied enum name
    """

    def __call__(self, v: T, *args: Any, **kwargs: Any) -> Any:
        """
        If it exists, returns the result of calling the
        method with the enumeration's name (lower-case).

        :param v: enumeration value to dispatch
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: method result (if found, else None)
        """

        method_name = v.name.lower()
        if hasattr(self, method_name):
            return getattr(self, method_name)(*args, **kwargs)

        return None
