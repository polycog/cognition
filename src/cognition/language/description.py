"""
Describing data types
"""

from typing import Optional, Union, cast, get_args, get_origin
from types import UnionType

from collections.abc import Sequence

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


def basemodel_field_doc(field_name: str, field_info: FieldInfo) -> str:
    """
    An base model field's name, type, and description

    :param field_name: field name
    :param field_info: field annotation information
    :return: "{name} ({type}[; {desc}])"
    """

    field_types: Sequence[type]
    if (
        isinstance(field_info.annotation, UnionType)
        or get_origin(field_info.annotation) is Union
    ):
        field_types = get_args(field_info.annotation)
    else:
        field_types = [cast(type, field_info.annotation)]

    types_names = " | ".join(t.__name__ for t in field_types)

    return f"{field_name} ({types_names}{ _sub_if(_t_sc, field_info.description) })"
