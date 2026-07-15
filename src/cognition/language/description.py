"""
Describing data types
"""

from typing import Optional

from string import Template

from enum import Enum

from ..util.enumeration import AutoDocEnum, DocEnum

#

_t_paren = Template(" ($s)")
# _t_sc = Template("; $s")


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
