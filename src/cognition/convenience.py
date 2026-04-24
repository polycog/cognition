"""
Practical library additions
"""

from typing import (
    Any,
    Optional,
    Protocol,
    TYPE_CHECKING,
    cast,
    runtime_checkable
)

from abc import ABC, abstractmethod

from collections.abc import (
    Iterable,
    Mapping,
)

from types import MappingProxyType

from enum import IntEnum

from functools import cmp_to_key

from cognition.functypes import (
    BiFunction,
    Predicate,
    TriFunction,
)

from cognition.utility import (
    ImplementsLessThan,
    optionally_name,
    stringify,
)

from cognition.core import (
    Action,
    ActionEvaluator,
    ActionFactory,
    ActionRank,
    Elaborator,
    IOContainer,
    Task,
)

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons

#

# default named action
# parameter to access
# the source operator
OPERATOR_SELF_PARAM: str = "_op"


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

    return optionally_name(_f, name)


def _qualified_name(name: str, **kwargs: Any) -> str:
    """
    Naming convention for a combo
    of name + optional params
    (ignoring those whose name
    starts with an underscore)
    """

    true_args = {
        k:v
        for k,v in kwargs.items()
        if k[:1] != '_'
    }

    if true_args:
        params_str = ", ".join(
            f"{k}={repr(v)}"
            for k,v in true_args.items()
        )

        return f"{name}[{params_str}]"

    return name

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

    new_f = stringify(_qualified_name(
        name,
        **kwargs
    ))(f)

    # pylint: disable=attribute-defined-outside-init
    new_named = cast(NamedAction, new_f)
    new_named.name = name
    new_named.params = MappingProxyType(kwargs.copy())

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

    @property
    def params(self) -> Mapping[str, Any]:
        """Optional augmentations in the name"""

class NamedOperator[S](ABC, Operator[S]):
    """
    Interface for an operator that
    implements the name property
    via supplied constructor parameter
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """
        Initializes the operator with a name and params
        """

        self._name = name
        self._params = MappingProxyType(kwargs.copy())

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

    @property
    def params(self) -> Mapping[str, Any]:
        """Implemented property"""

        return self._params


def add_operator[S](
    task: Task[S],
    op: Operator[S],
    self_param: Optional[str] = OPERATOR_SELF_PARAM
) -> tuple[ActionFactory[S], Action[S]]:
    """Produces an action factory from the operator"""

    factory_pred = op.can_perform

    act_params = dict(op.params)
    if self_param is not None:
        act_params[self_param] = op

    op_action = create_named_action(
        op.name,
        op.perform,
        **act_params
    )

    @task.action_factory
    @stringify(op.name)
    def action_factory(s: S, io: IOContainer) -> Iterable[Action[S]]:
        """propose performing if can perform"""

        if factory_pred(s, io):
            return [op_action]

        return []

    return action_factory, op_action


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

    return optionally_name(evaluation_func, name)


def sorting_evaluator[S](
    sorting_key: TriFunction[Action[S], S, IOContainer, "SupportsAllComparisons"],
    rank_start: int = 1,
    name: Optional[str] = None
) -> ActionEvaluator[S]:
    """
    Produces a convenience ActionEvaluator 
    that associates rankings based upon
    relative sorting order based upon
    a supplied key, starting with a
    supplied value
    """

    def evaluation_func(
        state: S,
        io: IOContainer,
        potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:

        ordered = sorted(
            potential_actions,
            key=lambda a: sorting_key(a, state, io)
        )

        current_rank: int = rank_start
        ranks = [current_rank] * len(ordered)

        for i in range(1, len(ordered)):
            key_curr = sorting_key(ordered[i], state, io)
            key_prev = sorting_key(ordered[i-1], state, io)

            if key_curr != key_prev:
                current_rank += 1

            ranks[i] = current_rank

        return (
            ActionRank(e, r)
            for e, r in zip(ordered, ranks)
        )

    return optionally_name(evaluation_func, name)

def operator_sorting_key[S](
    op_param: str = OPERATOR_SELF_PARAM
) -> TriFunction[Action[S], S, IOContainer, "SupportsAllComparisons"]:
    """
    Produces a sorting key
    for actions derived from
    named operators (using the
    supplied action parameter
    name)
    """

    def cmp(a: Action[S], b: Action[S]) -> int:
        op_a = cast(NamedAction, a).params[op_param]
        op_b = cast(NamedAction, b).params[op_param]

        if op_a == op_b:
            return 0

        if op_a < op_b:
            return -1

        return 1

    return lambda a, _s, _io: cmp_to_key(cmp)(a)
