"""
Knowledge representation
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
)

# ===


class TypedSchema(BaseModel):
    """Provides convenient access to schema type"""

    @property
    def type(self) -> str:
        """
        Access to schema type name

        :return: class name
        """

        return type(self).__name__


class Entity(TypedSchema):
    """
    Distinct object, concept, or event
    that is named and immutable
    """

    model_config = ConfigDict(frozen=True)
    name: str

    def __str__(self) -> str:
        """
        KR representation

        :return: e.type(name='e.name'[, e.field1=value1, ...])
        """

        cf = list(self.custom_fields)

        start = f"{self.type}(name={self.name}"
        if cf:
            return f"{start}, {", ".join(f"{k}={v}" for k,v in self.custom_fields)})"

        return f"{start})"

    @property
    def custom_fields(self) -> Iterable[tuple[str, Any]]:
        """
        Fields other than name

        :return: name/value pairs for non-name fields, if any
        """

        yield from ((k, v) for k, v in self.model_dump().items() if k != "name")


class BinaryRelation(TypedSchema):
    """
    A relationship between two entities
    """

    model_config = ConfigDict(frozen=True)
    entity1: Entity
    entity2: Entity

    def __str__(self) -> str:
        """
        KR representation

        :return: r.type(entity1=r.entity1, entity2=r.entity2[, r.field1=value1, ...])
        """

        cf = list(self.custom_fields)

        start = f"{self.type}(entity1={self.entity1}, entity2={self.entity2}"
        if cf:
            return (
                f"{start}, " f"{", ".join(f"{k}={v}" for k,v in self.custom_fields)})"
            )

        return f"{start})"

    @property
    def custom_fields(self) -> Iterable[tuple[str, Any]]:
        """
        Fields other than name

        :return: name/value pairs for non-name fields, if any
        """

        yield from (
            (k, v)
            for k, v in self.model_dump().items()
            if k not in ("entity1", "entity2")
        )


# ===

type Fact = Entity | BinaryRelation
"""Hashable typed schema for concepts and relationships"""
