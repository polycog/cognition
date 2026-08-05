"""
Describing data types
"""

from collections.abc import Iterable, Sequence
from enum import Enum
from string import Template
from types import UnionType
from typing import Union, cast, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo
from pydantic_ai import Agent as LanguageConvo
from pydantic_ai.models import Model

from ..knowledge.representation import BinaryRelation, Entity
from ..util.enumeration import AutoDocEnum, DocEnum

# ===

_t_paren = Template(" ($s)")
_t_sc = Template("; $s")


def _sub_if(t: Template, s: str | None) -> str:
    """
    Conditional substitution

    :param t: template to (potentially) use
    :param s: string to substitute, if not None
    :return: empty string if ``s`` is None; substituted template otherwise
    """
    return t.substitute(s=s.strip()) if s is not None else ""


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


def _is_union(annotation: type | None) -> bool:
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

    :param start_schema: source type
    :param deep: if ``True``, recursively includes base model fields
    :return: :class:`enum.Enum` and :class:`pydantic.BaseModel` types needed to understand the schema (including itself)
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

    # ===

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
    :param deep: if ``True``, recursively includes fields' types
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


# pylint: disable=too-few-public-methods
class FactDescriber[T: BaseModel]:
    """
    Describes a category of BaseModel instances.
    """

    def __init__(self, schema_type: type[T], task_desc: str | None) -> None:
        """
        :param schema_type: type for this describer
        :param task_desc: textual description of the task
        """

        task_prefix = ""
        if task_desc:
            task_prefix = f"== Context ==\n{ task_desc }\n\n"

        prompt_part1: str = (
            f"{task_prefix}"
            "== Task Description =="
            "\n"
            "Your task is to provide a 1-sentence description of a supplied fact."
            "\n\n"
            "== Object to Describe =="
            "\n"
        )

        class EgColor(AutoDocEnum):
            """
            Example choice of colors
            """

            RED = "the color red"
            GREEN = "the color green"
            BLUE = "the color blue"

        class EgBlock(Entity):
            """
            A block
            """

            name: str = Field(description="name of the block")
            color: EgColor = Field(description="block color")

        class EgSurface(Entity):
            """
            A surface for blocks
            """

            name: str = Field(description="name of the surface")

        class EgOnTop(BinaryRelation):
            """
            Represents spatial relations between blocks
            """

            entity1: EgBlock = Field(description="block on top")
            entity2: EgBlock | EgSurface = Field(
                description="block or surface below the block"
            )

        b1 = EgBlock(name="B1", color=EgColor.BLUE)
        b2 = EgBlock(name="B2", color=EgColor.RED)
        t = EgSurface(name="table")
        ot1 = EgOnTop(entity1=b1, entity2=b2)
        ot2 = EgOnTop(entity1=b2, entity2=t)

        prompt_part2: str = "".join(
            (
                "== Structural Description ==",
                "\n",
                basemodel_description(schema_type, True),
                "\n\n",
                "== Guiding Style ==",
                "\n",
                "* Do NOT use any markup or superfluous punctuation.\n",
                "* Do NOT reproduce the object in your description, nor its type, ",
                "nor explicitly refer to words like 'object', 'field', or 'attribute'.\n",
                "* Limit factual knowledge to the object and its structural description.\n",
                "\n",
                "== Example ==",
                "\n",
                "Given the following structural description...",
                "\n\n",
                basemodel_description(EgOnTop, True),
                "\n\n",
                "And the following additional known facts...",
                "\n\n",
                "\n".join(str(f) for f in (b1, b2, t, ot1, ot2)),
                "\n\n",
                "Good descriptions include...",
                "\n",
                f"* {b1 !s}",
                "\n",
                "  There is a block named 'B1' that has the color 'blue'",
                "\n",
                f"* {ot2 !s}",
                "\n",
                "  The red block named 'B2' is on top of the surface named 'table'",
            )
        )

        self._template = Template(f"{prompt_part1}$instance\n\n$others{prompt_part2}")

    def prompt(self, instance: T, others: Iterable[T]) -> str:
        """
        Produces the prompt for a supplied instance

        :param instance: instance to describe
        :return: resulting describer llm prompt
        """

        others_s = "\n".join(str(f) for f in others)
        if others_s:
            others_s = f"== Other Facts ==\n{others_s}\n\n"

        return self._template.substitute(instance=str(instance), others=others_s)

    def __call__(
        self, instance: T, others: Iterable[T], llm: Model, timeout_secs: int = 5
    ) -> str:
        """
        Describes the instance
        based upon a timeout budget.

        :param instance: instance to describe
        :param others: other facts for consideration
        :param llm: textual model to utilize
        :timeout_secs: time given per LLM call
        :return: description
        """

        return (
            LanguageConvo(
                model=llm,
                system_prompt="You are a helpful assistant.",
                model_settings={"timeout": timeout_secs},
            )
            .run_sync(self.prompt(instance, others))
            .output
        )

    @staticmethod
    def describe(
        instance: T,
        task_desc: str | None,
        others: Iterable[T],
        llm: Model,
        timeout_secs: int = 5,
    ) -> str:
        """
        One-off instantiation and calling of a describer

        :param instance: instance to describe
        :param task_desc: textual description of the task
        :param others: other facts for consideration
        :param llm: textual model to utilize
        :timeout_secs: time given per LLM call
        :return: description
        """

        return FactDescriber(type(instance), task_desc)(
            instance, others, llm, timeout_secs
        )
