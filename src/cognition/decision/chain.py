"""
Support for a decision process generated via an iterable value.
"""

import logging
from collections.abc import (
    Iterable,
    Iterator,
)
from dataclasses import dataclass
from typing import cast

from ..util.functypes import BiFunction
from ..util.misc import stringify
from .core import Action, IOContainer
from .dp import DecisionProcess

# ===

_logger = logging.getLogger(__name__)

# ===


@dataclass(frozen=True)
class Link[CV, CA]:
    """
    A link in a chained decision process
    """

    value: CV
    """current iterated value"""

    accumulator: CA | None
    """current (optional) user-accumulated value"""


class ChainState[CV, CA]:
    """
    State of a chained decision process

    Parameters represent...

    - ``CV``: type of iterated (v)alues
    - ``CA``: type of an optional (a)ccumulator
    """

    def __init__(self, chain: Iterable[CV], init_acc: CA | None = None):
        """
        :param chain: something iterable
        :param init_acc: (optional) initial accumulator value
        """
        self._iterator: Iterator[CV] = iter(chain)
        self._value: CV | None = None
        self._accumulator: CA | None = None

        self.next(init_acc)

    def __str__(self) -> str:  # pragma: no cover
        return f"ChainState(value=[{self._value}], acc=[{self._accumulator}])"

    @property
    def done(self) -> bool:
        """
        :return: ``True`` if the iterable (chain) has been exhausted
        """

        return self._value is None

    @property
    def current_link(self) -> Link[CV, CA] | None:
        """
        :return: current link in the chain, or ``None`` if exhausted
        """

        if self.done:
            return None

        return Link(cast(CV, self._value), self._accumulator)

    @property
    def accumulator(self) -> CA | None:
        """
        :return: current accumulator value
        """

        return self._accumulator

    def next(self, acc: CA | None) -> None:
        """
        Proceeds with the chain

        :param acc: optional new accumulator value
        """

        self._accumulator = acc
        self._value = next(self._iterator, None)


def create_chain_dp[CV, CA](
    chain: Iterable[CV],
    link_handler: BiFunction[Link[CV, CA], IOContainer, CA | None],
    init_accumulator: CA | None = None,
) -> DecisionProcess[ChainState[CV, CA]]:
    """
    Decision process via an iterable that with a handler at each value accumulating a result

    :param chain: sequence of values
    :param link_handler: function called at each chain link that can update the accumulator
    :param init_accumulator: initial (optional) accumulator value
    :return: produced decision process
    """

    _logger.info(
        "Generating a (chain) decision process: %s",
        chain,
    )
    _logger.debug(
        "handler=%s, acc=%s",
        link_handler,
        init_accumulator,
    )

    dp: DecisionProcess[ChainState[CV, CA]] = DecisionProcess(
        stringify("chain_start")(lambda: ChainState[CV, CA](chain, init_accumulator))
    )

    # ===

    @dp.action_factory
    @stringify("always_chaining")
    def action_factory(
        _s: ChainState[CV, CA], _io: IOContainer
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

            link: Link[CV, CA] | None = cs.current_link

            _logger.debug(
                "%s: link=%s, i=%s, o=%s",
                link_action,
                link,
                {k: str(v) for k, v in io.input.items()},
                {k: str(v) for k, v in io.output.items()},
            )

            if link is not None:
                cs.next(link_handler(link, io))

        return link_action

    @dp.termination_check
    @stringify("is_exhausted")
    def goal_check(cs: ChainState[CV, CA], _io: IOContainer) -> bool:
        """Checks if the chain is exhausted"""

        return cs.done

    # ===

    return dp
