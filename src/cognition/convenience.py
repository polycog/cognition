"""
Practical library additions
"""

from typing import (
    Any,
    Optional,
    Protocol,
    cast,
    runtime_checkable
)

from abc import ABC, abstractmethod

from collections.abc import (
    Iterable,
    Mapping,
)

from enum import IntEnum

from cognition.functypes import (
    BiFunction,
    Predicate,
)

from cognition.utility import (
    ImplementsLessThan,
    stringify,
)

from cognition.core import (
    Action,
    ActionEvaluator,
    ActionRank,
    Elaborator,
    IOContainer,
    Task,
)

#

class Rank(IntEnum):
    """
    Simple ordering of possible
    rankings of actions to pursue;
    sorting is used, so lower
    numbers are more important
    """

    HIGH = 1
    MEDIUM = 2
    LOW = 3


def create_elaborator[S](
    name: Optional[str] = None,
    **kwargs: BiFunction[S, IOContainer, Any]
) -> Elaborator[S]:
    """
    Produces an (optionally named)
    elaborator given association
    between keywords and functions
    """

    def _f(s: S, io: IOContainer) -> dict[str, Any]:
        return {
            k: v(s, io)
            for k, v in kwargs.items()
        }

    if name:
        return stringify(name)(_f)

    return _f


# pylint: disable=too-few-public-methods
@runtime_checkable
class NamedAction(Protocol):
    """
    Represents an action
    that has been augmented
    with some annotation
    """

    name: str
    params: Mapping[str, Any]

def create_named_action[S](
    name: str,
    f: Action[S],
    **kwargs: Any
) -> Action[S]:
    """
    Produces a function that has
    a nice __str__ and access to
    name via f.name and kwargs 
    via f.params
    """

    def qualified_name() -> str:
        if kwargs:
            params_str = ", ".join(f"{k}={repr(v)}" for k,v in kwargs.items())
            return f"{name}[{params_str}]"

        return name

    new_f = stringify(qualified_name())(f)

    # pylint: disable=attribute-defined-outside-init
    new_named = cast(NamedAction, new_f)
    new_named.name = name
    new_named.params = kwargs.copy()

    return new_f


class Operator[S](Protocol):
    """
    Convenience method for producing
    action factories that follow a
    common pattern of a predicate
    gating a single action
    """

    def can_perform(self, state: S, io: IOContainer) -> bool:
        """Does this hold in the current state/io?"""

    def perform(self, state: S, io: IOContainer) -> Optional[S]:
        """Then this action should be considered"""

    @property
    def name(self) -> str:
        """How to refer to the resulting action [and factory]"""


class NamedOperator[S](ABC, Operator[S]):
    """
    Interface for an operator that
    implements the name property
    via supplied constructor parameter
    """

    def __init__(self, name: str) -> None:
        """
        Initializes the operator with a name
        """

        self._name = name

    @abstractmethod
    def can_perform(self, state: S, io: IOContainer) -> bool:
        """Gating predicate"""

    @abstractmethod
    def perform(self, state: S, io: IOContainer) -> Optional[S]:
        """Resulting action"""

    @property
    def name(self) -> str:
        """Implemented property"""

        return self._name


def add_operator[S](task: Task[S], op: Operator[S]) -> None:
    """Produces an action factory from the operator"""

    @task.action_factory
    @stringify(op.name)
    def action_factory(s: S, io: IOContainer) -> Iterable[Action[S]]:
        """propose performing if can perform"""

        if op.can_perform(s, io):
            return [create_named_action(op.name, op.perform)]

        return []


def uniform_evaluator[S](
        r: ImplementsLessThan,
        p: Predicate[Action[S]] = lambda _: True,
        name: Optional[str] = None
    ) -> ActionEvaluator[S]:
    """
    Produces a convenience ActionEvaluator 
    that applies a supplied rank to all 
    potential actions that satisfy a predicate
    """

    def evaluation_func(
        _state: S,
        _io: IOContainer,
        potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:
        return (ActionRank(a, r) for a in potential_actions if p(a))

    if name:
        return stringify(name)(evaluation_func)

    return evaluation_func
