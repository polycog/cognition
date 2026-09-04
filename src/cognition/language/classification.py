"""
Selecting from amongst enumerated values
based upon natural language input
"""

import logging
from collections import Counter
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from string import Template
from typing import Any

from pydantic import BaseModel, create_model
from pydantic_ai import Agent as LanguageConvo
from pydantic_ai.models import Model

from .description import enum_item_doc, enum_name_doc

# ===

_logger = logging.getLogger(__name__)

# ===

DEFAULT_SCHEMA_FIELD_NAME: str = "value"
"""Default field name for response schema"""


@dataclass(frozen=True)
class EmpiricalConfidence:
    """
    Fractional confidence from
    a probabilistic process
    """

    selected: int
    """Number of positive outcomes"""

    trials: int
    """Number of opportunities"""

    def __float__(self) -> float:
        return self.selected / self.trials


def enum_schema(
    enum_type: type[Enum],
    field_name: str = DEFAULT_SCHEMA_FIELD_NAME,
) -> type[BaseModel]:
    """
    Produces a validation schema for
    producing an optional value
    from amongst a supplied enumerated type

    :param enum_type: type representing options
    :param field_name: schema field name for the enumerated type
    :return: resulting schema
    """

    fields_dict: dict[str, Any] = {field_name: enum_type | None}

    return create_model(enum_type.__name__, **fields_dict)


# pylint: disable=too-few-public-methods
class EnumClassifier[T: Enum]:
    """
    Function to classify an utterance (with confidence)
    with respect to an enumerated type.
    """

    def __init__(self, enum_type: type[T], task_desc: str | None) -> None:
        """
        :param enum_type: type representing options
        :param task_desc: textual description of the task
        """

        _logger.info(
            "Creating a classifier for type %s (task: %s)",
            enum_type.__name__,
            task_desc,
        )

        self._log_info = "".join(
            (
                f"{enum_type.__name__}",
                " (",
                ", ".join(str(member.value) for member in enum_type),
                ")",
            )
        )

        # ===

        self._schema = enum_schema(enum_type)

        # ===

        task_prefix = ""
        if task_desc:
            task_prefix = f"== Context ==\n{ task_desc }\n\n"

        prompt_prefix: str = "".join(
            (
                task_prefix,
                "== Task Description ==",
                "\n",
                "Your task is to select an option from the supplied schema ",
                "that best categorizes the utterance.",
                "\n\n",
                f"== Schema: { enum_name_doc(enum_type) } ==",
                "\n",
                "Each option below takes the form of valid JSON to return, ",
                "followed by a short description of its meaning.",
                "\n\n",
                "\n".join(
                    f"* { self._schema(value=item).model_dump_json() }\n  { enum_item_doc(item) }"
                    for item in enum_type
                ),
                "\n",
                f"* { self._schema(value=None).model_dump_json() }",
                "\n",
                "  the other values to not reasonably match the utterance",
                "\n\n",
                "== Utterance ==",
                "\n",
            )
        )
        prompt_postfix: str = (
            "\n\n\n"
            "Please choose a value that best matches the utterance."
            "\n"
            "Return ONLY valid JSON from the schema."
        )

        self._template = Template(f"{ prompt_prefix }$utterance{ prompt_postfix }")

    def prompt(self, utterance: str) -> str:
        """
        Produces the prompt for a supplied utterance

        :param utterance: user input
        :return: resulting classifier llm prompt
        """

        return self._template.substitute(utterance=utterance)

    def __call__(
        self, utterance: str, llm: Model, num_trials: int = 3, timeout_secs: int = 10
    ) -> tuple[T | None, EmpiricalConfidence]:
        """
        Classifies the utterance (with confidence)
        based upon a timeout budget.

        :param utterance: text to classify
        :param llm: textual model to utilize
        :param num_trials: number of classifications to perform & aggregate
        :timeout_secs: time given per LLM call
        :return: most common classification with confidence
        """

        _logger.info(
            "Attempting to classify utterance (%s) -> %s using %s",
            utterance,
            self._log_info,
            llm.model_name,
        )

        _logger.debug(
            "Trials=%s; timeout=%ss",
            num_trials,
            timeout_secs,
        )

        if num_trials < 1:
            e = ValueError("Must perform at least one trial")

            _logger.error(e)
            raise e

        convo = LanguageConvo(
            model=llm,
            output_type=self._schema,
            system_prompt="You are a helpful assistant.",
            model_settings={"timeout": timeout_secs},
        )

        prompt = self.prompt(utterance)

        results = []
        for t in range(num_trials):
            result = None

            _logger.debug("Trial %s: started", t)

            with suppress(Exception):
                result = convo.run_sync(prompt).output.value  # type: ignore

            _logger.debug("Trial %s: ended (result=%s)", t, result)

            results.append(result)

        top_result, top_count = Counter(results).most_common(1)[0]
        conf = EmpiricalConfidence(top_count, num_trials)

        _logger.info(
            "Classification: '%s' => %s (confidence=%s)", utterance, top_result, conf
        )

        return top_result, conf

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    @classmethod
    def classify(
        cls,
        utterance: str,
        enum_type: type[T],
        llm: Model,
        task_desc: str | None,
        num_trials: int = 3,
        timeout_secs: int = 10,
    ) -> tuple[T | None, EmpiricalConfidence]:
        """
        One-off instantiation and calling of a classifier

        :param utterance: text to classify
        :param enum_type: type representing options
        :param llm: textual model to utilize
        :param task_desc: textual description of the task
        :param num_trials: number of classifications to perform & aggregate
        :timeout_secs: time given per LLM call
        :return: most common classification with confidence
        """

        return cls(enum_type, task_desc)(utterance, llm, num_trials, timeout_secs)
