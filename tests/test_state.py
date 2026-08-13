"""
Tests for stage code
"""

import unittest
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cognition import (
    BaseDecisionProcess,
    DecisionProcess,
    IOContainer,
    MutableWrapper,
    Operator,
    PEState,
    Phase,
    PTEState,
    SelfElaborationState,
    SelfReinitState,
    stringify,
)

# ===


@dataclass
class ReinitSimple(SelfReinitState):
    """eg self-reinit with no logic"""

    num: int


# pylint: disable=too-few-public-methods
class ReinitCustomLogic(SelfReinitState):
    """eg self-reinit with logic"""

    def __init__(self, init_val: str) -> None:
        self.val = init_val
        self._excitement: int = 0

    def _reinit(self) -> None:
        self.val = f"{self.val}{ self._excitement * "!" }"
        self._excitement += 1

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.val}, {self._excitement})"


@dataclass
class ElabSimple(SelfElaborationState, SelfReinitState):
    """eg self-elab with no logic"""

    num: int


@dataclass
class ElabCustomLogic(SelfElaborationState, SelfReinitState):
    """eg self-elab with logic"""

    num: int

    def _elaborate(self, io: IOContainer) -> Mapping[str, Any]:
        return {
            "positive": self.num > 0,
            "even": self.num % 2 == 0,
            "cycle": io.i.clock.cycles,
        }


class PECounter(PEState[MutableWrapper[int]]):
    """eg PE state"""

    def __init__(self, init_val: int) -> None:
        super().__init__(MutableWrapper(init_val))

    def _elaborate(self, io: IOContainer) -> Mapping[str, Any]:
        return {
            "summary": f"{self.p.value} @ {io.i.clock.cycles}",
        }


class PTECounter(PTEState[MutableWrapper[int], MutableWrapper[int]]):
    """eg PTE state"""

    def __init__(self) -> None:
        super().__init__(
            MutableWrapper(0), stringify("reset_0")(lambda: MutableWrapper(0))
        )

    def _elaborate(self, io: IOContainer) -> Mapping[str, Any]:
        return {
            "summary": f"{self.t.value}:{self.p.value} @ {io.i.clock.cycles}",
        }


# ===


class TestState(unittest.TestCase):
    """Tests for state code"""

    def test_self_reinit(self) -> None:
        """
        test self reinit state
        """

        start_num = 42
        dp_simple = DecisionProcess(ReinitSimple(start_num))

        self.assertEqual(dp_simple.state.num, start_num)
        dp_simple.reinit()
        self.assertEqual(dp_simple.state.num, start_num)

        # ===

        start_phrase = "howdy"
        dp_custom = DecisionProcess(ReinitCustomLogic(start_phrase))

        self.assertEqual(dp_custom.state.val, start_phrase)
        dp_custom.reinit()
        self.assertEqual(dp_custom.state.val, f"{start_phrase}!")

    # pylint: disable=protected-access
    def test_self_elab(self) -> None:
        """
        test self elab state
        """

        state_simple = ElabSimple(42)
        dp_simple = DecisionProcess(state_simple)

        self.assertEqual(
            str(dp_simple),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={state_simple}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    (
                        "Elaborators="
                        f"{type(state_simple).ELABORATOR_NAME}({type(state_simple).__name__})"
                    ),
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertDictEqual(dict(state_simple._elab_values), {})

        dp_simple.run_phase()

        self.assertEqual(
            str(dp_simple),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={state_simple}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    (
                        "Elaborators="
                        f"{type(state_simple).ELABORATOR_NAME}({type(state_simple).__name__})"
                    ),
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertDictEqual(dict(state_simple._elab_values), {})

        # ===

        state_custom = ElabCustomLogic(51)
        dp_custom = DecisionProcess(state_custom)

        self.assertEqual(
            str(dp_custom),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={state_custom}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    (
                        "Elaborators="
                        f"{type(state_simple).ELABORATOR_NAME}({type(state_custom).__name__})"
                    ),
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertDictEqual(dict(state_custom._elab_values), {})

        dp_custom.run_phase()

        self.assertEqual(
            str(dp_custom),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={state_custom}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    (
                        "Elaborators="
                        f"{type(state_simple).ELABORATOR_NAME}({type(state_custom).__name__})"
                    ),
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertDictEqual(
            dict(state_custom._elab_values),
            {
                "positive": True,
                "even": False,
                "cycle": dp_custom.num_cycles,
            },
        )

        dp_custom.reinit()

        self.assertDictEqual(dict(state_custom._elab_values), {})

    def test_pte(self) -> None:
        """
        test pte state
        """

        c = PTECounter()

        self.assertEqual(c.p.value, 0)
        self.assertEqual(c.t.value, 0)

        with self.assertRaises(AttributeError):
            _ = c.e.summary

        # ===

        dp = DecisionProcess(c)

        upper_t = 10

        # pylint: disable=unused-variable
        @dp.operator("inner")
        class InnerOp(Operator[PTECounter]):
            """increment t counter"""

            def can_perform(self, state: PTECounter, _io: IOContainer) -> bool:
                return state.t.value < upper_t

            def perform(self, state: PTECounter, _io: IOContainer) -> None:
                state.t.value += 1

        # pylint: disable=unused-variable
        @dp.operator("outer", terminal=True)
        class OuterOp(Operator[PTECounter]):
            """increment p counter"""

            def can_perform(self, state: PTECounter, _io: IOContainer) -> bool:
                return state.t.value >= upper_t

            def perform(self, state: PTECounter, _io: IOContainer) -> None:
                state.p.value += 1

        dp.run_phase()

        self.assertEqual(c.p.value, 0)
        self.assertEqual(c.t.value, 0)
        self.assertEqual(c.e.summary, f"{c.t.value}:{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PTECounter(p={MutableWrapper(c.p.value)}; t={MutableWrapper(c.t.value)}; e={_d})",
        )

        dp.run_until_done()

        self.assertEqual(c.p.value, 1)
        self.assertEqual(c.t.value, upper_t)
        self.assertEqual(c.e.summary, f"{c.t.value}:{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PTECounter(p={MutableWrapper(c.p.value)}; t={MutableWrapper(c.t.value)}; e={_d})",
        )

        dp.reinit()

        self.assertEqual(c.p.value, 1)
        self.assertEqual(c.t.value, 0)

        with self.assertRaises(AttributeError):
            _ = c.e.summary

        _d = {}
        self.assertEqual(
            str(c),
            f"PTECounter(p={MutableWrapper(c.p.value)}; t={MutableWrapper(c.t.value)}; e={_d})",
        )

        dp.run_until_done()

        self.assertEqual(c.p.value, 2)
        self.assertEqual(c.t.value, upper_t)
        self.assertEqual(c.e.summary, f"{c.t.value}:{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PTECounter(p={MutableWrapper(c.p.value)}; t={MutableWrapper(c.t.value)}; e={_d})",
        )

    def test_pe(self) -> None:
        """
        test pe state
        """

        start_val = 42
        c = PECounter(start_val)

        self.assertEqual(c.p.value, start_val)
        self.assertIsNone(c.t)

        with self.assertRaises(AttributeError):
            _ = c.e.summary

        # ===

        dp = DecisionProcess(c)

        # pylint: disable=unused-variable
        @dp.operator("inc", terminal=True)
        class IncOp(Operator[PECounter]):
            """increment counter"""

            def can_perform(self, _state: PECounter, _io: IOContainer) -> bool:
                return True

            def perform(self, state: PECounter, _io: IOContainer) -> None:
                state.p.value += 1

        dp.run_phase()

        self.assertEqual(c.p.value, start_val)
        self.assertIsNone(c.t)
        self.assertEqual(c.e.summary, f"{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PECounter(p={MutableWrapper(c.p.value)}; t={c.t}; e={_d})",
        )

        dp.run_until_done()

        self.assertEqual(c.p.value, start_val + 1)
        self.assertIsNone(c.t)
        self.assertEqual(c.e.summary, f"{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PECounter(p={MutableWrapper(c.p.value)}; t={c.t}; e={_d})",
        )

        dp.reinit()

        self.assertEqual(c.p.value, start_val + 1)
        self.assertIsNone(c.t)

        with self.assertRaises(AttributeError):
            _ = c.e.summary

        _d = {}
        self.assertEqual(
            str(c),
            f"PECounter(p={MutableWrapper(c.p.value)}; t={c.t}; e={_d})",
        )

        dp.run_until_done()

        self.assertEqual(c.p.value, start_val + 2)
        self.assertIsNone(c.t)
        self.assertEqual(c.e.summary, f"{c.p.value} @ {dp.num_cycles}")

        _d = {"summary": c.e.summary}
        self.assertEqual(
            str(c),
            f"PECounter(p={MutableWrapper(c.p.value)}; t={c.t}; e={_d})",
        )
