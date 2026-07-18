"""
Tests for chain code
"""

from typing import cast

from enum import StrEnum, auto

import unittest

from cognition import (
    ChainState,
    EnumDispatch,
    create_chain_dp,
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

            result = cast(
                ChainState[int, int],
                create_chain_dp(
                    range(n),
                    lambda link, _io: cast(int, link.accumulator) * (link.value + 1),
                    1,
                )(),
            )

            self.assertIsNone(result.current_link)

            return cast(int, result.accumulator)

        #

        self.assertEqual(my_fact(0), 1)

        self.assertEqual(my_fact(5), 1 * 2 * 3 * 4 * 5)

        self.assertEqual(my_fact(7), 1 * 2 * 3 * 4 * 5 * 6 * 7)

    def test_dftba(self) -> None:
        """
        Chaining without accumulator
        """

        self.assertEqual(
            create_chain_dp(
                NerdFighter,
                lambda link, io: print(
                    link.value.value[0].lower(), end="", file=io.o.log
                ),
            )
            .run_until_done()
            .log,
            "dftba",
        )

    def test_dftba_dispatch(self) -> None:
        """
        Chaining to dispatch -> values
        """

        class Project(EnumDispatch[NerdFighter]):
            """
            Segmenting operations by enum value
            """

            def __init__(self) -> None:
                self._result: list[str] = []

            @property
            def result(self) -> str:
                """put it together"""
                return " + ".join(self._result)

            def don_t(self) -> None:
                """d"""
                self._result.append("care")

            def forget(self) -> None:
                """f"""
                self._result.append("create")

            def to(self) -> None:
                """t"""
                self._result.append("cultivate")

            def be(self) -> None:
                """b"""
                self._result.append("empower")

            def awesome(self) -> None:
                """a"""
                self._result.append("learn")

        pfa = Project()
        create_chain_dp(NerdFighter, lambda link, _io: pfa(link.value))()
        self.assertEqual(pfa.result, "care + create + cultivate + empower + learn")
