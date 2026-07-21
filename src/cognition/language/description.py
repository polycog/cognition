"""
Describing data types
"""

from typing import Optional, Union, cast, get_args, get_origin
from types import UnionType

from collections.abc import Iterable, Sequence

from string import Template

from enum import Enum

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from ..util.enumeration import AutoDocEnum, DocEnum

#

_t_paren = Template(" ($s)")
_t_sc = Template("; $s")


def _sub_if(t: Template, s: Optional[str]) -> str:
    """
    Conditional substitution

    :param t: template to (potentially) use
    :param s: string to substitute, if not None
    :return: empty string if `s` is None; substituted template otherwise
    """
    return t.substitute(s=s) if s is not None else ""


def enum_name_doc(enum_type: type[Enum]) -> str:
    """
    An enumeration's name and doc string

    :param enum_type: type to describe
    :return: "{name}[ ({doc})]"
    """

    return f"{ enum_type.__name__ }{ _sub_if(_t_paren, enum_type.__doc__) }"


def enum_item_doc(enum_item: Enum) -> str:
    """
    An enumeration item's value and doc string

    :param enum_item: item to describe
    :return: "{value}[ ({doc})]"
    """

    extra = enum_item.__doc__ if isinstance(enum_item, (DocEnum, AutoDocEnum)) else None
    return f"{ enum_item.value }{ _sub_if(_t_paren, extra) }"


def enum_description(enum_type: type[Enum]) -> str:
    """
    Description of an enumerated type
    and its members

    :param enum_type: type to describe
    :return: type description
    """

    lines = []

    lines.append(f"Enumeration: { enum_name_doc(enum_type) }, options...")

    for item in enum_type:
        lines.append(f"* { enum_item_doc(item) }")

    return "\n".join(lines)


def basemodel_name_doc(schema_type: type[BaseModel]) -> str:
    """
    A base model's name and description

    :param schema_type: type to describe
    :return: "{name}[ ({desc})]"
    """

    schema_json = schema_type.model_json_schema()

    return (
        f"{schema_json['title']}{ _sub_if(_t_paren, schema_json.get('description')) }"
    )


def _is_union(annotation: Optional[type]) -> bool:
    return isinstance(annotation, UnionType) or (get_origin(annotation) is Union)


def basemodel_field_doc(field_name: str, field_info: FieldInfo) -> str:
    """
    A base model field's name, type, and description

    :param field_name: field name
    :param field_info: field annotation information
    :return: "{name} ({type}[; {desc}])"
    """

    field_types: Sequence[type]
    if _is_union(field_info.annotation):
        field_types = get_args(field_info.annotation)
    else:
        field_types = [cast(type, field_info.annotation)]

    types_names = " | ".join(t.__name__ for t in field_types)

    return f"{field_name} ({types_names}{ _sub_if(_t_sc, field_info.description) })"


def basemodel_dep_types(start_schema: type[BaseModel], deep: bool) -> Iterable[type]:
    """
    Accounts for a base model's dependent types

    :param schema_type: source type
    :param deep: if `True`, recursively includes base model fields
    :return: Enum and BaseModel types needed to understand the schema (including itself)
    """

    def _supported_type(t: type) -> bool:
        return issubclass(t, BaseModel) or issubclass(t, Enum)

    def _basemodel_field_types(schema_type: type[BaseModel]) -> Iterable[type]:
        for f_a in (
            f_i.annotation
            for f_i in schema_type.model_fields.values()
            if f_i.annotation is not None
        ):

            candidates: Iterable[type]
            if _is_union(f_a):
                candidates = get_args(f_a)
            else:
                candidates = [f_a]

            yield from (t for t in candidates if _supported_type(t))

    #

    todo: list[type] = [start_schema]
    explored: set[type] = set()

    result: list[type] = [start_schema]
    added: set[type] = {start_schema}

    while todo:
        t = todo.pop(0)
        if t not in explored:
            explored.add(t)

            for field_type in _basemodel_field_types(t):
                if field_type not in added:
                    result.append(field_type)
                    added.add(field_type)

                if deep and issubclass(field_type, BaseModel):
                    todo.append(field_type)

    return result


def basemodel_description(schema_type: type[BaseModel], deep: bool) -> str:
    """
    Description of an basemodel type
    and its members

    :param schema_type: type to describe
    :param deep: if `True`, recursively includes fields' types
    :return: type description
    """

    lines: list[str] = []

    todo = basemodel_dep_types(schema_type, deep)

    for t in todo:
        if lines:
            lines.append("")

        if issubclass(t, BaseModel):
            lines.append(f"Base Model: { basemodel_name_doc(t) }, fields...")
            for f_n, f_i in t.model_fields.items():
                lines.append(f"* { basemodel_field_doc(f_n, f_i) }")

        elif issubclass(t, Enum):
            lines.append(enum_description(t))

    return "\n".join(lines)
