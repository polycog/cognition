"""
Practical library additions
"""

from typing import Iterable

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
