"""
Support for a task sequence 
generated via an iterable value.
"""

from typing import (
    Iterable,
    Iterator,
    Optional,
    cast,
)

from dataclasses import dataclass

from cognition.functypes import BiFunction

from cognition.utility import stringify

from cognition.core import (
    Action,
    IOContainer,
    Task,
)

#

@dataclass(frozen=True)
class Link[CV, CA]:
    """
    A link in a chained task, consisting of...
    - value: current iterated value
    - accumulator: current user-accumulated value
    """

    value: CV
    accumulator: Optional[CA]


class ChainState[CV, CA]:
    """
    State of a chained task, parameterized by...
    - C: type of iterated values
    - A: type of an (optional) accumulator
    """

    def __init__(self, chain: Iterable[CV], init_acc: Optional[CA] = None):
        """
        Initializes the chain, with...
        - chain: something iterable
        - init_acc: optionally an initial accumulator value
        """
        self._iterator: Iterator[CV] = iter(chain)
        self._value: Optional[CV] = None
        self._accumulator: Optional[CA] = None

        self.next(init_acc)

    def __str__(self) -> str: # pragma: no cover
        """attempting to make human-readable"""

        return (
            "ChainState("
            f"value=[{self._value}], "
            f"acc=[{self._accumulator}]"
            ")"
        )

    @property
    def done(self) -> bool:
        """
        Indicates if the chain has been fully iterated
        """

        return self._value is None

    @property
    def current_link(self) -> Optional[Link[CV, CA]]:
        """
        Produces the current link in the chain,
        or None if the chain has been exhausted
        """

        if self.done:
            return None

        return Link(cast(CV, self._value), self._accumulator)

    @property
    def accumulator(self) -> Optional[CA]:
        """
        Produces the current accumulator value
        """

        return self._accumulator

    def next(self, acc: Optional[CA]) -> None:
        """
        Proceeds down the chain with a new
        (optional) accumulated value
        """

        self._accumulator = acc
        self._value = next(self._iterator, None)


def create_chain_task[CV, CA](
    chain: Iterable[CV],
    link_handler: BiFunction[Link[CV, CA], IOContainer, Optional[CA]],
    init_accumulator: Optional[CA] = None,
) -> Task[ChainState[CV, CA]]:
    """
    Produces a task based upon supplied...
    - chain: iterable to unravel the execution sequence
    - link_handler: function to call at each link
                    (that optionally updates the accumulator)
    - init_accumulator: initial (optional) accumulator value
    """

    @stringify("always_chaining")
    def action_factory(
        _s: ChainState[CV, CA],
        _io: IOContainer
    ) -> Action[ChainState[CV, CA]]:
        """
        Always produce an action to try
        to make progress in the chain
        """

        @stringify("next_link")
        def link_action(cs: ChainState[CV, CA], io: IOContainer) -> None:
            """
            Make progress in the chain
            (if not exhausted)
            """

            link: Optional[Link[CV, CA]] = cs.current_link

            if link is not None:
                cs.next(
                    link_handler(link, io)
                )

        return link_action

    @stringify("is_exhausted")
    def goal_check(cs: ChainState[CV, CA], _io: IOContainer) -> bool:
        """Checks if the chain is exhausted"""

        return cs.done

    #

    t: Task[ChainState[CV, CA]] = Task(
        lambda: ChainState[CV, CA](chain, init_accumulator)
    )

    t.add_action_factory(action_factory)
    t.add_goal_check(goal_check)

    return t
