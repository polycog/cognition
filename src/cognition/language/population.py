"""
Filling a data structure with values
based upon natural language input
"""

import logging
from string import Template

from pydantic import BaseModel
from pydantic_ai import Agent as LanguageConvo
from pydantic_ai.models import Model

from .description import basemodel_description

# ===

_logger = logging.getLogger(__name__)

# ===


# pylint: disable=too-few-public-methods
class ModelPopulator[T: BaseModel]:
    """
    Function to instantiate a model with values based upon an utterance
    """

    def __init__(self, model_type: type[T], task_desc: str | None) -> None:
        """
        :param model_type: type needing instantiation
        :param task_desc: textual description of the task
        """

        _logger.info(
            "Creating a populator for type %s (task: %s)",
            model_type.__name__,
            task_desc,
        )

        self._schema = model_type

        task_prefix = ""
        if task_desc:
            task_prefix = f"== Context ==\n{ task_desc }\n\n"

        prompt_prefix: str = "".join(
            (
                task_prefix,
                "== Task Description ==",
                "\n",
                "Your task is to instantiate the supplied schema with ",
                "values that best match the supplied utterance.",
                "\n\n",
                "== Schema Description ==",
                "\n",
                basemodel_description(model_type, True),
                "\n\n",
                "== Utterance ==",
                "\n",
            )
        )

        prompt_postfix: str = (
            "\n\n\n"
            "Please choose field values that best matches the utterance."
            "\n"
            "Return ONLY valid JSON from the schema."
        )

        self._template = Template(
            f"{prompt_prefix}$utterance\n\n$extra{prompt_postfix}"
        )

    def prompt(self, utterance: str, *extra: str) -> str:
        """
        Produces the prompt for a supplied utterance

        :param utterance: user input
        :param extra: dynamic extra context to supply
        :return: resulting filler llm prompt
        """

        extra_s = ""
        if extra:
            extra_s = "\n".join(f"* {e}" for e in extra)
            extra_s = f"== Extra Information ==\n{extra_s}\n\n"

        return self._template.substitute(utterance=utterance, extra=extra_s)

    def __call__(
        self,
        utterance: str,
        llm: Model,
        *extra: str,
        timeout_secs: int = 10,
    ) -> T:
        """
        Produces a model instance
        based upon a timeout budget.

        :param utterance: text to instantiate
        :param llm: textual model to utilize
        :param extra: dynamic extra context to supply
        :timeout_secs: time given per LLM call
        :return: model instance
        """

        _logger.info(
            "Attempting to populate utterance (%s) -> %s using %s",
            utterance,
            self._schema.__name__,
            llm.model_name,
        )

        _logger.debug(
            "timeout=%ss; extra=%s",
            timeout_secs,
            extra,
        )

        result = (
            LanguageConvo(
                model=llm,
                system_prompt="You are a helpful assistant.",
                model_settings={"timeout": timeout_secs},
                output_type=self._schema,
            )
            .run_sync(self.prompt(utterance, *extra))
            .output
        )

        _logger.info("Populate: '%s' => %r", utterance, result)

        return result

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    @classmethod
    def populate(
        cls,
        utterance: str,
        model_type: type[T],
        llm: Model,
        task_desc: str | None,
        *extra: str,
        timeout_secs: int = 10,
    ) -> T:
        """
        One-off instantiation and calling of a populator

        :param utterance: text to classify
        :param model_type: type needing instantiation
        :param llm: textual model to utilize
        :param task_desc: textual description of the task
        :param extra: dynamic extra context to supply
        :timeout_secs: time given per LLM call
        :return: most common classification with confidence
        """

        return cls(model_type, task_desc)(
            utterance, llm, *extra, timeout_secs=timeout_secs
        )
