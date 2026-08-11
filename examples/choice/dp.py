"""
Decision process for making choices
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Self, cast

from cognition import (
    ActionEvaluator,
    ActuatorInvoker,
    IOContainer,
    NamedObject,
    OperatorGenerator,
    Rank,
    sorting_evaluator,
    uniform_evaluator,
)

from env import ChoiceEnvironment

# ===


@dataclass
class ChosenField:
    """
    State: field of focus
    """

    field_name: str | None = None


# ===


class ChooseFieldGenerator(OperatorGenerator[ChosenField, ChoiceEnvironment[Any]]):
    """
    Dynamically proposes focus on
    fields that have not yet been
    decided
    """

    def __init__(self, field_name: str) -> None:
        """
        :param field_name: proposed field name
        """

        super().__init__(
            field=field_name
        )  # proposed actions are annotated with their field
        self._f = field_name

    @classmethod
    def get_name(cls) -> str:
        return "choose_field"

    @classmethod
    def generate(
        cls, state: ChosenField, io: IOContainer, extra: ChoiceEnvironment[Any]
    ) -> Iterable[Self]:
        if state.field_name is not None:
            yield from ()  # don't propose if working on another field
        else:
            for field_name in extra.fields_reader(io).options:
                if extra.reader(field_name)(io).choice is None:
                    yield cls(field_name)  # only propose valid fields without a choice

    def perform(self, state: ChosenField, io: IOContainer) -> None:
        state.field_name = self._f


# ===


class ChooseValueGenerator(OperatorGenerator[ChosenField, ChoiceEnvironment[Any]]):
    """
    Dynamically propose value options
    for the chosen field
    """

    def __init__(
        self, field_name: str, field_value: str, invoker: ActuatorInvoker[str, bool]
    ) -> None:
        """
        :param field_name: proposed field name
        :param field_value: proposed field value
        :param invoker: method by which to enact the choice
                        (if selected)
        """

        super().__init__(
            field=field_name, value=field_value, terminal=True
        )  # proposed actions are annotated with their field/value
        # terminal to reflect sensor change

        self._v = field_value
        self._i = invoker

    @classmethod
    def get_name(cls) -> str:
        return "choose_value"

    @classmethod
    def generate(
        cls, state: ChosenField, io: IOContainer, extra: ChoiceEnvironment[Any]
    ) -> Iterable[Self]:
        if state.field_name is None:
            yield from ()  # don't propose if not working on a field
        else:
            invoker = extra.invoker(state.field_name)  # invoker for this field

            # propose all valid values to choose
            for field_value in extra.reader(state.field_name)(io).options:
                yield cls(state.field_name, field_value, invoker)

    def perform(self, state: ChosenField, io: IOContainer) -> None:
        self._i(io, self._v)


# ===

random_field_selection = uniform_evaluator(
    Rank.MEDIUM,
    lambda a: cast(NamedObject, a).name == ChooseFieldGenerator.get_name(),
    name="random_field_order",
)


def field_sorting(default: int, **field: int) -> ActionEvaluator[ChosenField]:
    """
    Produces an ordering over field selection

    :param default: ranking to supply any unnamed field
    :param field: mapping of field name to rank (lower is more important)
    :return: produced evaluator
    """

    return sorting_evaluator(
        lambda a, _s, _io: field.get(cast(NamedObject, a).params["field"], default),
        lambda a: cast(NamedObject, a).name == ChooseFieldGenerator.get_name(),
        name="sorted_field_order",
    )


# ===

random_value_selection = uniform_evaluator(
    Rank.MEDIUM,
    lambda a: cast(NamedObject, a).name == ChooseValueGenerator.get_name(),
    name="random_value_selection",
)


def lookahead_sorting(env: ChoiceEnvironment[Any]) -> ActionEvaluator[ChosenField]:
    """
    Produces a partial ordering over value selection,
    simply preferring acceptable assignments via
    1-step lookahead of the resulting configuration

    :param env: associated choice environment
    :return: produced evaluator
    """

    def _acc_via_simulation(a: NamedObject) -> bool:
        return env.container.copy(  # type: ignore[no-any-return]
            (a.params["field"], a.params["value"])
        ).acceptable

    return sorting_evaluator(
        lambda a, _s, _io: 1 if _acc_via_simulation(cast(NamedObject, a)) else 10,
        lambda a: cast(NamedObject, a).name == ChooseValueGenerator.get_name(),
        name="sorted_value_order",
    )
