"""
Describing data types
"""

import logging
from collections.abc import Iterable, Sequence
from enum import Enum
from string import Template
from types import GenericAlias, UnionType
from typing import Union, cast, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo
from pydantic_ai import Agent as LanguageConvo
from pydantic_ai.models import Model

from ..knowledge.representation import BinaryRelation, Entity
from ..util.enumeration import AutoDocEnum, DocEnum

# ===

_logger = logging.getLogger(__name__)

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

    _logger.debug(
        "%s(%s): doc=%s",
        enum_name_doc.__name__,
        enum_type.__name__,
        enum_type.__doc__,
    )

    return f"{ enum_type.__name__ }{ _sub_if(_t_paren, enum_type.__doc__) }"


def enum_item_doc(enum_item: Enum) -> str:
    """
    An enumeration item's value and doc string

    :param enum_item: item to describe
    :return: "{value}[ ({doc})]"
    """

    _logger.debug(
        "%s(%s): mro=%s, doc=%s",
        enum_item_doc.__name__,
        enum_item,
        type(enum_item).__mro__,
        enum_item.__doc__,
    )

    extra = enum_item.__doc__ if isinstance(enum_item, (DocEnum, AutoDocEnum)) else None
    return f"{ enum_item.value }{ _sub_if(_t_paren, extra) }"


def enum_description(enum_type: type[Enum]) -> str:
    """
    Description of an enumerated type
    and its members

    :param enum_type: type to describe
    :return: type description
    """

    members = tuple(item for item in enum_type)

    _logger.debug(
        "%s(%s): members=(%s)", enum_description.__name__, enum_type.__name__, members
    )

    lines = []

    lines.append(f"Enumeration: { enum_name_doc(enum_type) }, options...")

    for item in members:
        lines.append(f"* { enum_item_doc(item) }")

    return "\n".join(lines)


def basemodel_name_doc(schema_type: type[BaseModel]) -> str:
    """
    A base model's name and description

    :param schema_type: type to describe
    :return: "{name}[ ({desc})]"
    """

    _logger.debug(
        "%s(%s)",
        basemodel_name_doc.__name__,
        schema_type.__name__,
    )

    schema_json = schema_type.model_json_schema()

    _logger.debug(schema_json)

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

    is_union = _is_union(field_info.annotation)

    _logger.debug(
        "%s(%s, %s): is_union=%s, desc=%s",
        basemodel_field_doc.__name__,
        field_name,
        field_info,
        is_union,
        field_info.description,
    )

    field_types: Sequence[type]
    if is_union:
        field_types = get_args(field_info.annotation)
    else:
        field_types = [cast(type, field_info.annotation)]

    _logger.debug(
        "field types: %s",
        field_types,
    )

    def _name(thing: type | GenericAlias) -> str:
        if isinstance(thing, GenericAlias):
            origin = get_origin(thing)
            args = ", ".join(_name(a) for a in get_args(thing))

            return f"{origin.__name__}[{args}]"

        return thing.__name__

    types_names = " | ".join(_name(t) for t in field_types)

    return f"{field_name} ({types_names}{ _sub_if(_t_sc, field_info.description) })"


def basemodel_dep_types(
    start_schema: type[BaseModel] | Iterable[type[BaseModel]], deep: bool
) -> Iterable[type]:
    """
    Accounts for a base model's dependent types

    :param start_schema: source type(s)
    :param deep: if ``True``, recursively includes base model fields
    :return: :class:`enum.Enum` and :class:`pydantic.BaseModel` types
             needed to understand the schema (including itself)
    """

    def _supported_type(t: type) -> bool:
        origin = get_origin(t)
        t = t if origin is None else origin

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

    start: tuple[type, ...]

    if not isinstance(start_schema, Iterable):
        start = (start_schema,)
    else:
        start = tuple(start_schema)

    todo: list[type] = list(start)

    # ===

    _logger.debug(
        "%s(%s; deep=%s): start",
        basemodel_dep_types.__name__,
        ", ".join(s.__name__ for s in start),
        deep,
    )

    # ===

    explored: set[type] = set()

    result: list[type] = []
    for s in start:
        if s not in result:
            result.append(s)

    added: set[type] = set(start)

    while todo:
        t = todo.pop(0)
        already_explored = t in explored

        _logger.debug(
            "Consider type: %s (already_explored=%s)", t.__name__, already_explored
        )

        if not already_explored:
            explored.add(t)

            _logger.debug("Type added to explored: %s", explored)

            for field_type in _basemodel_field_types(t):

                already_in_result = field_type in added
                _logger.debug(
                    "Consider field type: %s (already_in_result=%s, mro=%s)",
                    field_type.__name__,
                    already_in_result,
                    field_type.__mro__,
                )

                if not already_in_result:
                    result.append(field_type)
                    added.add(field_type)

                if deep and issubclass(field_type, BaseModel):
                    todo.append(field_type)

                    _logger.debug("Field type added to TODO: %s", todo)

    # ===

    _logger.debug(
        "%s(%s; deep=%s): done (explored=%s, result=%s)",
        basemodel_dep_types.__name__,
        ", ".join(s.__name__ for s in start),
        deep,
        explored,
        result,
    )

    return result


def basemodel_description(
    schema_types: type[BaseModel] | Iterable[type[BaseModel]], deep: bool
) -> str:
    """
    Description of basemodel type(s)
    and their members

    :param schema_types: type(s) to describe
    :param deep: if ``True``, recursively includes fields' types
    :return: description
    """

    start: tuple[type, ...]

    if not isinstance(schema_types, Iterable):
        start = (schema_types,)
    else:
        start = tuple(schema_types)

    # ===

    _logger.debug(
        "%s(%s; deep=%s)",
        basemodel_description.__name__,
        ", ".join(s.__name__ for s in start),
        deep,
    )

    # ===

    lines: list[str] = []

    todo = basemodel_dep_types(start, deep)

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


# ===


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
    entity2: EgBlock | EgSurface = Field(description="block or surface below the block")


_B1 = EgBlock(name="B1", color=EgColor.BLUE)
_B2 = EgBlock(name="B2", color=EgColor.RED)
_T = EgSurface(name="table")
_OT1 = EgOnTop(entity1=_B1, entity2=_B2)
_OT2 = EgOnTop(entity1=_B2, entity2=_T)


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

        _logger.info(
            "Creating a describer for fact type %s (task: %s)",
            schema_type.__name__,
            task_desc,
        )

        # ===

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
                "\n".join(str(f) for f in (_B1, _B2, _T, _OT1, _OT2)),
                "\n\n",
                "Good descriptions include...",
                "\n",
                f"* {_B1 !s}",
                "\n",
                "  There is a block named 'B1' that has the color 'blue'",
                "\n",
                f"* {_OT2 !s}",
                "\n",
                "  The red block named 'B2' is on top of the surface named 'table'",
            )
        )

        self._template = Template(
            f"{prompt_part1}$instance\n\n$extra$others{prompt_part2}"
        )

    def prompt(self, instance: T, others: Iterable[T], *extra: str) -> str:
        """
        Produces the prompt for a supplied instance

        :param instance: instance to describe
        :param others: other facts for consideration
        :param extra: dynamic extra context to supply
        :return: resulting describer llm prompt
        """

        others_s = "\n".join(str(f) for f in others)
        if others_s:
            others_s = f"== Other Facts ==\n{others_s}\n\n"

        extra_s = ""
        if extra:
            extra_s = "\n".join(f"* {e}" for e in extra)
            extra_s = f"== Extra Information ==\n{extra_s}\n\n"

        return self._template.substitute(
            instance=str(instance), others=others_s, extra=extra_s
        )

    def __call__(
        self,
        instance: T,
        others: Iterable[T],
        llm: Model,
        *extra: str,
        timeout_secs: int = 5,
    ) -> str:
        """
        Describes the instance
        based upon a timeout budget.

        :param instance: instance to describe
        :param others: other facts for consideration
        :param llm: textual model to utilize
        :param extra: dynamic extra context to supply
        :param timeout_secs: time given per LLM call
        :return: description
        """

        others_t = tuple(others)

        _logger.info(
            "Describing instance (%s) using %s",
            instance,
            llm.model_name,
        )

        _logger.debug(
            "type=%s, timeout=%ss; others=%s; extra=%s",
            type(instance).__name__,
            timeout_secs,
            others_t,
            extra,
        )

        result = (
            LanguageConvo(
                model=llm,
                system_prompt="You are a helpful assistant.",
                model_settings={"timeout": timeout_secs},
            )
            .run_sync(self.prompt(instance, others_t, *extra))
            .output
        )

        _logger.info("Description: '%s'", result)

        return result

    @classmethod
    def describe(
        cls,
        instance: T,
        task_desc: str | None,
        others: Iterable[T],
        llm: Model,
        *extra: str,
        timeout_secs: int = 5,
    ) -> str:
        """
        One-off instantiation and calling of a describer

        :param instance: instance to describe
        :param task_desc: textual description of the task
        :param others: other facts for consideration
        :param llm: textual model to utilize
        :param extra: dynamic extra context to supply
        :parm timeout_secs: time given per LLM call
        :return: description
        """

        return cls(type(instance), task_desc)(
            instance, others, llm, *extra, timeout_secs=timeout_secs
        )


def describe_facts(
    instances: Iterable[BaseModel],
    task_desc: str | None,
    llm: Model,
    timeout_secs: int = 5,
    debug: bool = False,
) -> str:
    """
    One-off description of a supplied set of facts

    :param instance: instance(s) to describe
    :param task_desc: textual description of the task
    :param llm: textual model to utilize
    :param timeout_secs: time given per LLM call
    :param debug: returns the prompt instead of the description
    :return: description (or prompt it debug)
    """

    facts = tuple(instances)

    _logger.info(
        "Describing instances (%s) using %s (timeout=%ss)",
        ", ".join(f"{f!s}" for f in instances),
        llm.model_name,
        timeout_secs,
    )

    task_prefix = ""
    if task_desc:
        task_prefix = f"== Context ==\n{ task_desc }\n\n"

    prompt: str = (
        f"{task_prefix}"
        "== Task Description =="
        "\n"
        "Your task is to provide a concise description of a supplied set of facts."
        "\n\n"
        "== Objects to Describe =="
        "\n"
        f"{"\n".join(str(f) for f in facts)}"
        "\n\n"
        "== Structural Description =="
        "\n"
        f"{basemodel_description((type(f) for f in facts), True)}"
        "\n\n"
        "== Guiding Style =="
        "\n"
        "* Do NOT use any markup or superfluous punctuation.\n"
        "* Do NOT reproduce an object in its description, nor its type, "
        "nor explicitly refer to words like 'object', 'field', or 'attribute'.\n"
        "* Limit factual knowledge to the objects and the structural description.\n"
        "* If possible, and effective in communication, "
        "do not provide a separate sentence for each fact, "
        "but rather combine them into an appropriate set of summative statement(s).\n"
        "\n"
        "== Example =="
        "\n"
        "Given the following structural description..."
        "\n\n"
        f"{basemodel_description(EgOnTop, True)}"
        "\n\n"
        "Good descriptions include..."
        "\n"
        f"* ({_B1 !s},)"
        "\n"
        "  There is a block named 'B1' that has the color 'blue'"
        "\n"
        f"* ({_OT2 !s},)"
        "\n"
        "  The red block named 'B2' is on top of the surface named 'table'"
        "\n"
        f"* ({_OT1 !s}, {_OT2 !s},)"
        "\n"
        "  The blue block named 'B1' is on top of the red block named 'B2', "
        "which is on top of the surface named 'table'"
    )

    if debug:
        return prompt

    result = (
        LanguageConvo(
            model=llm,
            system_prompt="You are a helpful assistant.",
            model_settings={"timeout": timeout_secs},
        )
        .run_sync(prompt)
        .output
    )

    _logger.info("Description: '%s'", result)

    return result
