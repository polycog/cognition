"""
Utility code
"""

from typing import (
    Any,
    Callable,
    Mapping,
    Protocol,
)

from functools import wraps

#

class AttrReferral:
    """
    Utility class to allow an external
    dictionary { key:value } to provide
    .key read-only access to value
    """

    _ref_field_name: str = '_attr_mapping'

    #

    def __init__(self, external_source: Mapping[str, Any]) -> None:
        """
        Provides a reference to the external mapping
        of valid attribute names to associated
        values
        """

        object.__setattr__(
            self,
            AttrReferral._ref_field_name,
            external_source
        )


    def __getattr__(self, key: str) -> Any:
        """
        Implements .key access, as mediated
        by the mapping supplied during
        initialization
        """

        if key not in self.__getattribute__(AttrReferral._ref_field_name):
            raise AttributeError(f"Contains no such key: '{key}'")

        return self.__getattribute__(AttrReferral._ref_field_name)[key]


    def __setattr__(self, key: str, value: Any) -> None:
        """
        Enforces read-only access
        """

        raise AttributeError(f"'{type(self).__name__}' object attributes are read-only.")


# pylint: disable=too-few-public-methods
class ImplementsLessThan(Protocol):
    """
    Dictates a sortable type for
    purposes of action ranking
    """

    def __lt__(self, other: Any) -> bool:
        ...


class StringifiedFunction[**P, R]:
    """
    A callable object that wraps a function
    and provides a custom __str__ representation.
    """

    def __init__(self, func: Callable[P, R], str_representation: str):
        """
        Wrapping function and __str__
        representation
        """

        wraps(func)(self)
        self._func: Callable[P, R] = func
        self._str_representation: str = str_representation

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Calls the original function
        """
        return self._func(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns the custom string representation
        """

        return self._str_representation

# pylint: disable=invalid-name
def stringify[**P, R](str_representation: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for stringifying
    a function
    """

    def decorated(func: Callable[P, R]) -> Callable[P, R]:
        """Newly stringified function"""

        return StringifiedFunction(func, str_representation)

    return decorated
