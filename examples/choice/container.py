"""
Choice container defn
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, replace
from enum import Enum
from types import NoneType, UnionType
from typing import Self, final, get_args

# ===


@dataclass
class ChoiceContainer(ABC):
    """
    A special case of a data class in which
    all fields are assumed to take the value
    of either an enumeration or ``None`` -
    together these fields form a set of choices
    to be made.
    """

    @final
    @property
    def field_names(self) -> Iterable[str]:
        """
        :return: names of all fields
                (i.e., choices to be made)
        """

        yield from (f.name for f in fields(self))

    @final
    @property
    def done(self) -> bool:
        """
        :return: ``True`` if all fields have non-``None`` values
        """

        return all(f_val is not None for f_val in asdict(self).values())

    @final
    @property
    def acceptable(self) -> bool:
        """
        Determines if the choices made satisfy domain constraints

        :return: ``True`` if :meth:``done`` and satisfies constraints
        """

        return self.done and self._acceptable

    @property
    @abstractmethod
    def _acceptable(self) -> bool:
        """
        Override opportunity to provide custom domain
        constraints to :meth:``acceptable``

        :return: ``True`` if satisfies constraints
        """

    @final
    def reset(self) -> Self:
        """
        Set all field values to ``None``

        :return: self-reference (for chaining)
        """

        for f in self.field_names:
            setattr(self, f, None)

        return self

    @final
    def choice_type(self, f_name: str) -> type[Enum]:
        """
        Given the name of a field,
        produce the (non-``None``) type

        :param f_name: field name
        :return: associated enumeration class
        :raises AttributeError: invalid field name
        :raises TypeError: field does not comply with container assumptions
        """

        f_dict = {f.name: f.type for f in fields(self)}

        if f_name not in f_dict:
            raise AttributeError

        f_t = f_dict[f_name]

        if not isinstance(f_t, UnionType):
            raise TypeError

        opts = tuple(opt for opt in get_args(f_t) if opt is not NoneType)
        if len(opts) != 1:
            raise TypeError

        opt = opts[0]
        if (not isinstance(opt, type)) or (not issubclass(opt, Enum)):
            raise TypeError

        return opt

    @final
    def copy(self, *simulate: tuple[str, str]) -> Self:
        """
        Produces a copy of this container instance
        with any number of field-value_name changes

        :param simulate: (field, value_name) change to induce within the copy
        :return: produced copy
        """

        result = replace(self)

        for f, v in simulate:
            f_t = self.choice_type(f)
            result = replace(result, **{f: f_t[v]})

        return result
