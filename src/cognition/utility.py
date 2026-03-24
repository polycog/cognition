"""
Utility code
"""

from typing import Any, Mapping, Protocol

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


    def __setattr__(self, key, value) -> None:
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

    def __lt__(self, other) -> bool:
        ...
