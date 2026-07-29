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
    Phase,
    SelfElaborationState,
    SelfReinitState,
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
                    (
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
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
                    (
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
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
                    (
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
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
                    (
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
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
