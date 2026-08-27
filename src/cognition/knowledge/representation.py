"""
Knowledge representation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from string import Template
from typing import Any, ClassVar, Protocol, Self, cast, final, runtime_checkable

from pydantic import BaseModel, Field, create_model

from ..util.functypes import Supplier
from ..util.misc import TypedMixin, is_list, is_set

# ===


# pylint: disable=too-few-public-methods
@runtime_checkable
class Freezable(Protocol):
    """Produces an immutable version"""

    def freeze(self) -> Self:
        """
        :return: immutable version
        """


# pylint: disable=too-few-public-methods
@runtime_checkable
class Thawable[T](Protocol):
    """Produces a mutable version"""

    def thaw(self) -> T:
        """
        :return: mutable version
        """


# ===


class BaseSchema(TypedMixin, BaseModel, ABC):
    """
    Freezable base model with a fixed set of required (immutable) fields.

    As necessary, provides support to freeze custom fields via
    (a) automatic detection of list->tuple, set->frozenset; or
    (b) recursive freezing via :class:`Freezable`; or
    (c) subtype implementations of `freeze_fieldname` method.

    Frozen instance is a subtype that is then thawable to produce
    a copy of the original instance.
    """

    @classmethod
    @abstractmethod
    def fixed_field_names(cls) -> tuple[str, ...]:
        """
        :return: frozen required field names
        """

    @final
    @property
    def custom_fields(self) -> Iterable[tuple[str, Any]]:
        """
        Non-fixed fields

        :return: name/value pairs for non-required fields, if any
        """

        yield from (
            (k, v)
            for k, v in self.model_dump().items()
            if k not in type(self).fixed_field_names()
        )

    def __str__(self) -> str:
        """
        KR representation

        :return: e.type(fixed1='e.fixed1'[, ...][, custom1=e.custom1, ...])
        """

        cf = list(self.custom_fields)
        ff = ", ".join(f"{f}={getattr(self, f)}" for f in self.fixed_field_names())

        start = f"{self.type}({ff}"
        if cf:
            return f"{start}, {", ".join(f"{k}={v}" for k,v in self.custom_fields)})"

        return f"{start})"

    def replace(self, **fields: Any) -> Self:
        """
        Produces a copy with optional field changes

        :param fields: name=new value
        :return: copy
        :raises KeyError: invalid (non-required) field
        :raises ValidationError: violates schema
        """

        allowed_to_change = tuple(f for f, _ in self.custom_fields)

        for k in fields:
            if k not in allowed_to_change:
                raise KeyError(f"{k} is not a custom field in {type(self).__name__}")

        new_obj = self.model_copy(update=fields)
        type(self).model_validate(new_obj.model_dump(), strict=True)

        if isinstance(self, Thawable):
            object.__setattr__(
                new_obj, "thaw", lambda: self.thaw().model_copy(update=fields)
            )

        return new_obj

    # ===

    @staticmethod
    def __is_field_frozen(field_name: str, t: type[BaseSchema]) -> bool:
        if field_name not in t.model_fields:
            return False

        return t.model_fields[field_name].frozen or t.model_config.get("frozen", False)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        # enforces that required fields are immutable
        for ff in cls.fixed_field_names():
            if not BaseSchema.__is_field_frozen(ff, cls):
                raise TypeError(f"Field {ff} must be frozen in subclass {cls.__name__}")

    # ===

    CUSTOM_FREEZE_METHOD: ClassVar[Template] = Template("freeze_$field")
    """field name (via ``field`` parameter)-> custom freeze method name"""

    @staticmethod
    def __method_if_exists(src_obj: object, field_name: str) -> Supplier[Any] | None:
        method_name = BaseSchema.CUSTOM_FREEZE_METHOD.substitute(field=field_name)

        if callable(getattr(src_obj, method_name, None)):
            return cast(Supplier[Any], getattr(src_obj, method_name))

        return None

    # ===

    __frozen_t: ClassVar[type[Self] | None] = None
    """maintaining the first-created type to support equality of frozen instances"""

    @final
    def freeze(self) -> Self:
        """
        See :class:`Freezable`
        """

        field_cache: dict[str, Any] = {}

        def _freeze_field_type(
            src: object, name: str, orig: type[Any] | None
        ) -> type[Any]:
            if orig is None:
                orig = type(getattr(src, name))

            meth = type(self).__method_if_exists(src, name)
            if meth is None:
                if is_list(orig):
                    meth = (
                        lambda: tuple(  # pylint: disable=unnecessary-lambda-assignment
                            getattr(src, name)
                        )
                    )
                elif is_set(orig):
                    meth = lambda: frozenset(  # pylint: disable=unnecessary-lambda-assignment
                        getattr(src, name)
                    )

            if meth is not None:
                value = meth()
                field_cache[name] = value
                return type(value)

            return orig

        field_source: dict[str, type[Any] | None] = {
            name: field.annotation for name, field in type(self).model_fields.items()
        }

        if self.model_extra:
            field_source |= {name: None for name in self.model_extra}

        annotation_data = {
            name: _freeze_field_type(self, name, info)
            for name, info in field_source.items()
        }

        # ===

        if self.__frozen_t is None:
            type(self).__frozen_t = create_model(  # type: ignore
                f"Frozen{self.type}",
                __base__=type(self),
                __config__={"frozen": True},
                **annotation_data,
            )
        assert self.__frozen_t is not None

        # ===

        def _freeze_field_value(name: str, orig: Any, contents: dict[str, Any]) -> Any:
            if isinstance(orig, Freezable):
                return orig.freeze()

            return field_cache.get(name, contents)

        value_data = {
            name: _freeze_field_value(name, getattr(self, name), value)
            for name, value in self.model_dump().items()
        }

        # ===

        frozen = self.__frozen_t(**value_data)  # pylint: disable=not-callable
        self_cp = self.model_copy()

        object.__setattr__(frozen, "thaw", lambda: self_cp)

        return frozen


# ===


class Entity(BaseSchema):
    """
    Distinct object, concept, or event
    that is named
    """

    name: str = Field(frozen=True)

    # ===

    @final
    @classmethod
    def fixed_field_names(cls) -> tuple[str, ...]:
        return ("name",)


class BinaryRelation(BaseSchema):
    """
    A relationship between two entities
    """

    entity1: Entity = Field(frozen=True)
    entity2: Entity = Field(frozen=True)

    # ===

    @final
    @classmethod
    def fixed_field_names(cls) -> tuple[str, ...]:
        return (
            "entity1",
            "entity2",
        )


# ===

type Fact = Entity | BinaryRelation
"""Graphical representation of concepts and relationships"""
