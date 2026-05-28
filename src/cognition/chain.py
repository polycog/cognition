"""
Support for a task sequence generated via an iterable value.
"""

from typing import (
    Optional,
    cast,
)

from collections.abc import (
    Iterable,
    Iterator,
)

from dataclasses import dataclass

from .functypes import BiFunction

from .utility import stringify

from .core import (
    Action,
    IOContainer,
    Task,
)

#

@dataclass(frozen=True)
class Link[CV, CA]:
    """
    A link in a chained task
    """

    value: CV
    """current iterated value"""

    accumulator: Optional[CA]
    """current (optional) user-accumulated value"""


class ChainState[CV, CA]:
    """
    State of a chained task

    Parameters represent...
    
    - CV: type of iterated (v)alues
    - CA: type of an optional (a)ccumulator
    """

    def __init__(self, chain: Iterable[CV], init_acc: Optional[CA] = None):
        """
        :param chain: something iterable
        :param init_acc: (optional) initial accumulator value
        """
        self._iterator: Iterator[CV] = iter(chain)
        self._value: Optional[CV] = None
        self._accumulator: Optional[CA] = None

        self.next(init_acc)

    def __str__(self) -> str: # pragma: no cover
        return (
            "ChainState("
            f"value=[{self._value}], "
            f"acc=[{self._accumulator}]"
            ")"
        )

    @property
    def done(self) -> bool:
        """
        :return: ``True`` if the iterable (chain) has been exhausted
        """

        return self._value is None

    @property
    def current_link(self) -> Optional[Link[CV, CA]]:
        """
        :return: current link in the chain, or ``None`` if exhausted
        """

        if self.done:
            return None

        return Link(cast(CV, self._value), self._accumulator)

    @property
    def accumulator(self) -> Optional[CA]:
        """
        :return: current accumulator value
        """

        return self._accumulator

    def next(self, acc: Optional[CA]) -> None:
        """
        Proceeds with the chain

        :param acc: optional new accumulator value
        """

        self._accumulator = acc
        self._value = next(self._iterator, None)


def create_chain_task[CV, CA](
    chain: Iterable[CV],
    link_handler: BiFunction[Link[CV, CA], IOContainer, Optional[CA]],
    init_accumulator: Optional[CA] = None,
) -> Task[ChainState[CV, CA]]:
    """
    Produces a sequential task to exhaust an iterable

    :param chain: sequence of values
    :param link_handler: function called at each chain link that can update the accumulator
    :param init_accumulator: initial (optional) accumulator value
    """

    t: Task[ChainState[CV, CA]] = Task(
        lambda: ChainState[CV, CA](chain, init_accumulator)
    )

    #

    @t.action_factory
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

    @t.goal_check
    @stringify("is_exhausted")
    def goal_check(cs: ChainState[CV, CA], _io: IOContainer) -> bool:
        """Checks if the chain is exhausted"""

        return cs.done

    #

    return t
