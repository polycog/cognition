"""
Practical library additions
"""

from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
)

from enum import IntEnum

from cognition.functypes import Predicate

from cognition.utility import ImplementsLessThan

from cognition.core import (
    Action,
    ActionEvaluator,
    ActionRank,
    IOContainer,
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


class NamedAction[S]:
    """
    Convenience wrapper around
    a function to facilitate
    human-readable naming
    """

    def __init__(self, name: str, f: Action, **kwargs: Any) -> None:
        """
        Constructs the action
        with a name and function
        to execute when this
        object is called,
        as well as an optional
        list of key=value pairs
        to parameterize
        """

        self._name = name
        self._f = f
        self._params = kwargs.copy()

    def __str__(self) -> str:
        """
        Either Name or Name[k1=v1, k2=v2, ...]
        """

        if self._params:
            params_str = ", ".join(f"{k}={repr(v)}" for k,v in self._params.items())
            return f"{self._name}[{params_str}]"

        return self._name

    @property
    def name(self) -> str:
        """Gets the name"""

        return self._name

    @property
    def params(self) -> Mapping[str, Any]:
        """Gets the params"""

        return self._params

    def __call__(self, s: S, io: IOContainer) -> Optional[S]:
        """Execute the action"""

        return self._f(s, io)


def uniform_evaluator[S](
        r: ImplementsLessThan,
        p: Predicate[Action[S]] = lambda _: True,
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

    return evaluation_func
