"""
Tests for core code
"""

import unittest
from collections.abc import Iterable
from io import StringIO
from math import sqrt
from typing import Any, cast

from cognition import (
    Action,
    ActionFactory,
    ActionRank,
    AttrReferral,
    BaseDecisionProcess,
    DecisionProcessErrorMessage,
    DecisionProcessExecutionError,
    IOContainer,
    Phase,
    Rank,
    TerminationCheck,
    create_elaborator,
    create_named_action,
    stringify,
)

# ===

TERMINATION_NAME: str = "prime_or_perfect"
FACTORY_NAME: str = "always_inc"
ELAB_NAME: str = "prime_and_perfect"


def _make_term(a_perfect: str, a_prime: str) -> TerminationCheck[int]:
    """
    Create the perfect/prime termination check
    given the supplied elaboration
    attributes
    """

    @stringify(TERMINATION_NAME)
    def pred(_: int, io: IOContainer) -> bool:
        v_perfect = cast(bool, getattr(io.i.elaboration, a_perfect))

        v_prime = cast(bool, getattr(io.i.elaboration, a_prime))

        return v_perfect or v_prime

    return pred


def _is_prime(number: int) -> bool:
    """
    Determines if a supplied integer is prime (slowly)
    """
    if number <= 1:
        return False

    for i in range(2, int(sqrt(number)) + 1):
        if number % i == 0:
            return False

    return True


def _make_increment_factory(a_name: str) -> ActionFactory[int]:
    """
    Create the increment factory
    given the supplied action name
    """

    @stringify(FACTORY_NAME)
    def factory(_state: int, _io: IOContainer) -> Action[int]:

        @stringify(a_name)
        def inc(num: int, _: IOContainer) -> int:
            return num + 1

        return inc

    return factory


class ListInputOutput:
    """confirms simple input/output scheme"""

    def __init__(self) -> None:
        """make the encapsulated list"""

        self._data: list[str] = []

    @property
    def data(self) -> list[str]:
        """input access to list contents"""

        return self._data.copy()

    def add(self, item: str) -> None:
        """adds to the list"""

        self._data.append(item)


class TestCore(unittest.TestCase):
    """Tests for core code"""

    def test_func_vs_imp(self) -> None:
        """Confirms flexible action execution"""

        dp_f: BaseDecisionProcess[list[str]] = BaseDecisionProcess(lambda: ["hi"])

        self.assertEqual(dp_f.state, ["hi"])

        dp_f.add_action_factory(lambda _s, _io: [lambda s, _: s[1:]]).run_cycles()

        self.assertEqual(dp_f.state, [])

        # ===

        dp_i: BaseDecisionProcess[list[str]] = BaseDecisionProcess(lambda: ["hi"])

        self.assertEqual(dp_i.state, ["hi"])

        def a(s: list[str], _io: IOContainer) -> None:
            del s[0]

        dp_i.add_action_factory(lambda _s, _io: a).run_cycles()

        self.assertEqual(dp_i.state, [])

    def test_elab_dec(self) -> None:
        """Confirms elaborator decoration"""

        word = "test"
        dp: BaseDecisionProcess[str] = BaseDecisionProcess(lambda: word)

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={word}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    "Elaborators=",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        # ===

        e_name = "echo"

        @dp.elaborator
        @stringify(e_name)
        def echo(s: str, _io: IOContainer) -> dict[str, Any]:
            return {e_name: s}

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={word}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    f"Elaborators={e_name}",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        # ===

        g_name = f"check_{e_name}"

        @dp.termination_check
        @stringify(g_name)
        def check_echo(_s: str, io: IOContainer) -> bool:
            e_result = cast(
                str,
                getattr(
                    cast(
                        AttrReferral,
                        getattr(io.i, BaseDecisionProcess.INPUT_KEY_ELABORATION),
                    ),
                    e_name,
                ),
            )

            return e_result == word

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={word}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={g_name}",
                    f"Elaborators={e_name}",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        dp.run_until_done()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={word}",
                    f"Done?={True}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={g_name}",
                    f"Elaborators={e_name}",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

    def test_phase(self) -> None:
        """Confirms phase sequencing"""

        self.assertEqual(Phase.ELABORATION.next, Phase.TERMINATIONCHECK)

        self.assertEqual(Phase.TERMINATIONCHECK.next, Phase.PROPOSE)

        self.assertEqual(Phase.PROPOSE.next, Phase.RANK)

        self.assertEqual(Phase.RANK.next, Phase.APPLY)

        self.assertEqual(Phase.APPLY.next, Phase.ELABORATION)

    def test_basics(self) -> None:
        """Confirms some decision process basics"""

        a_inc = create_named_action("inc", lambda s, _io: s + 1)

        a_dec = create_named_action("dec", lambda s, _io: s - 1)

        ar_inc_low = ActionRank(a_inc, Rank.LOW)
        self.assertEqual(str(ar_inc_low), "ActionRank(a=inc, r=3)")

        ar_dec_high = ActionRank(a_dec, Rank.HIGH)
        self.assertEqual(str(ar_dec_high), "ActionRank(a=dec, r=1)")

        self.assertTrue(ar_dec_high < ar_inc_low)

        with self.assertRaises(TypeError):
            _ = ar_dec_high < "not an ActionRank"

        # ===

        starting_point: int = 100

        dp: BaseDecisionProcess[int] = BaseDecisionProcess(lambda: starting_point)

        # no actions yet!
        with self.assertRaises(DecisionProcessExecutionError) as cm:
            for _ in dp.phases():
                pass

        self.assertEqual(cm.exception.msg, DecisionProcessErrorMessage.NO_PROPOSAL)

        self.assertEqual(
            str(cm.exception), DecisionProcessErrorMessage.NO_PROPOSAL.value
        )

        dp.reinit()

        # ===

        dp.add_action_factory(lambda _s, _io: [a_inc, a_dec])

        # no evaluation of multiple possibilities
        with self.assertRaises(DecisionProcessExecutionError) as cm:
            for _ in dp.cycles():
                pass

        self.assertEqual(cm.exception.msg, DecisionProcessErrorMessage.NO_RANK)

        self.assertEqual(str(cm.exception), DecisionProcessErrorMessage.NO_RANK.value)

        # ===

        dp.add_action_evaluator(lambda _s, _io, _actions: [])

        # ===

        @dp.action_evaluator
        def dec_over_inc(
            _s: int, _io: IOContainer, actions: Iterable[Action[int]]
        ) -> Iterable[ActionRank[int]]:
            """Always prefer dec over inc"""

            return [
                ar_inc_low if a == a_inc else ar_dec_high
                for a in actions
                if a in (a_dec, a_inc)
            ]

        dp.run_cycles()

        self.assertEqual(dp.state, starting_point - 1)
        self.assertEqual(dp.num_cycles, 2)

        # ===

        dp.add_termination_check(lambda s, _io: s == starting_point - 2)

        for _ in dp.cycles():
            pass

        self.assertEqual(dp.state, starting_point - 2)
        self.assertEqual(dp.num_cycles, 3)

    def test_io(self) -> None:
        """Confirming basic io functionality"""

        starting_point: int = 1

        lst_name: str = "lst"
        lst = ListInputOutput()

        dp_io: BaseDecisionProcess[int] = BaseDecisionProcess(lambda: starting_point)

        self.assertEqual(
            str(dp_io),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={starting_point}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    "Elaborators=",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        # add as both input/output
        dp_io.set_input_data(lst_name, lst).set_output_channel(lst_name, lst)

        self.assertIs(getattr(dp_io.io.o, lst_name), lst)
        self.assertIsNot(getattr(dp_io.io.i, lst_name).data, lst.data)
        self.assertListEqual(lst.data, [])
        self.assertListEqual(getattr(dp_io.io.i, lst_name).data, lst.data)

        # confirm registration
        self.assertEqual(
            str(dp_io),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={starting_point}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    "Elaborators=",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}, {lst_name}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}, {lst_name}",
                )
            ),
        )

        def inc_and_add_and_log(s: int, io: IOContainer) -> int:
            """
            * logs a combo of sensed data
            * adds sensed data to another output channel
            * progresses the decision process
            """

            sensed: str = str(cast(ListInputOutput, getattr(io.i, lst_name)).data)
            cast(ListInputOutput, getattr(io.o, lst_name)).add(str(s))

            log: StringIO = cast(
                StringIO, getattr(io.o, BaseDecisionProcess.OUTPUT_KEY_LOG)
            )
            cycle: int = getattr(
                getattr(io.i, BaseDecisionProcess.INPUT_KEY_TIME),
                BaseDecisionProcess.INPUT_ATTR_TIME,
            )

            print(f"@{cycle}: data={sensed}", file=log)

            return s + 1

        a_name: str = "go"
        a_go = create_named_action(a_name, inc_and_add_and_log)

        factory_name: str = f"{a_name} factory"

        @stringify(factory_name)
        def go_action_factory(_s: int, _io: IOContainer) -> Action[int]:
            """always go!"""

            return a_go

        dp_io.add_action_factory(go_action_factory)

        goal_diff: int = 3
        goal_name: str = f"{a_name} check {goal_diff}"

        @stringify(goal_name)
        def go_goal(s: int, _io: IOContainer) -> bool:
            """end after k increments"""

            return s == starting_point + goal_diff

        dp_io.add_termination_check(go_goal).run_until_done()

        self.assertIs(getattr(dp_io.io.o, lst_name), lst)
        self.assertIsNot(getattr(dp_io.io.i, lst_name).data, lst.data)
        self.assertListEqual(
            lst.data,
            [str(n) for n in range(starting_point, starting_point + goal_diff)],
        )
        self.assertListEqual(getattr(dp_io.io.i, lst_name).data, lst.data)

        # confirm ability to remove input/output
        dp_io.set_input_data(lst_name, None).set_output_channel(lst_name, None)

        self.assertEqual(
            str(dp_io),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={starting_point + goal_diff}",
                    f"Done?={True}",
                    f"Chosen={a_name}",
                    f"Action Factories={factory_name}",
                    f"Potential Actions={a_name}",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        # confirm logging
        self.assertEqual(
            dp_io.log,
            # ruff: ignore[FLY002]
            "\n".join(("@1: data=[]", "@2: data=['1']", "@3: data=['1', '2']", "")),
        )

    def test_count(self) -> None:
        """Confirming simple decision process execution"""

        starting_point: int = 1_001
        next_perfect_prime: int = 1_009

        e_prime: str = "prime"
        e_perfect: str = "perfect"
        a_inc: str = "inc"

        # ===

        dp_count_until: BaseDecisionProcess[int] = (
            BaseDecisionProcess(lambda: starting_point)
            .add_termination_check(_make_term(e_perfect, e_prime))
            .add_elaborator(
                create_elaborator(
                    ELAB_NAME,
                    **{
                        e_prime: lambda s, _: _is_prime(s),
                        e_perfect: lambda s, _: sqrt(s) % 1 == 0,
                    },
                )
            )
            .add_action_factory(_make_increment_factory(a_inc))
        )

        self.assertEqual(dp_count_until.num_cycles, 0)

        self.assertEqual(dp_count_until.state, starting_point)

        self.assertFalse(dp_count_until.done)

        self.assertEqual(dp_count_until.phase, Phase.ELABORATION)

        self.assertIsNone(dp_count_until.chosen_action)

        self.assertEqual(
            str(dp_count_until),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={starting_point}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    f"Action Factories={FACTORY_NAME}",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={TERMINATION_NAME}",
                    f"Elaborators={ELAB_NAME}",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )

        dp_count_until.run_until_done()

        self.assertEqual(dp_count_until.num_cycles, 9)

        self.assertEqual(dp_count_until.state, next_perfect_prime)

        self.assertTrue(dp_count_until.done)

        self.assertEqual(dp_count_until.phase, Phase.TERMINATIONCHECK)

        self.assertEqual(dp_count_until.chosen_action, a_inc)

        self.assertEqual(
            str(dp_count_until),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={next_perfect_prime}",
                    f"Done?={True}",
                    f"Chosen={a_inc}",
                    f"Action Factories={FACTORY_NAME}",
                    f"Potential Actions={a_inc}",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={TERMINATION_NAME}",
                    f"Elaborators={ELAB_NAME}",
                    (
                        f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}, "
                        f"{BaseDecisionProcess.INPUT_KEY_ELABORATION}"
                    ),
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                )
            ),
        )
