"""
Tests for chain code
"""

from typing import cast

from enum import StrEnum, auto

import unittest

from cognition import (
    ChainState,
    Task,
    create_chain_task,
)

#

class NerdFighter(StrEnum):
    """Words to live by!"""

    DON_T = auto()
    FORGET = auto()
    TO = auto()
    BE = auto()
    AWESOME = auto()


class TestChain(unittest.TestCase):
    """Tests for chain code"""

    def test_mult_acc(self) -> None:
        """
        Numeric accumulation -> fact
        """

        def my_fact(n: int) -> int:
            """factorial via chaining"""

            t: Task[ChainState[int, int]] = create_chain_task(
                range(n),
                lambda link, _io: cast(int, link.accumulator) * (link.value + 1),
                1
            )

            t.run_until_done()
            self.assertIsNone(t.state.current_link)

            return cast(int, t.state.accumulator)

        #

        self.assertEqual(
            my_fact(0),
            1
        )

        self.assertEqual(
            my_fact(5),
            1 * 2 * 3 * 4 * 5
        )

        self.assertEqual(
            my_fact(7),
            1 * 2 * 3 * 4 * 5 * 6 * 7
        )


    def test_dftba(self) -> None:
        """
        Chaining without accumulator
        """

        t: Task[ChainState[NerdFighter, None]] = create_chain_task(
            NerdFighter,
            lambda link, io: print(
                link.value.value[0].lower(),
                end="",
                file=io.o.log
            )
        )

        t.run_until_done()

        self.assertEqual(
            t.log,
            "dftba"
        )
