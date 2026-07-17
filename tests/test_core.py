"""
Tests for core code
"""

from typing import Any, cast

from collections.abc import Iterable

from math import sqrt

import unittest

from io import StringIO

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
    TimeSensor,
    create_elaborator,
    create_named_action,
    stringify,
)

#

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


class ListSensorActuator:
    """confirms simple sensor/actuator scheme"""

    def __init__(self) -> None:
        """make the encapsulated list"""

        self._data: list[str] = []

    @property
    def data(self) -> list[str]:
        """sensor access to list contents"""

        return self._data.copy()

    def add(self, item: str) -> None:
        """adds to the list"""

        self._data.append(item)


class TestTask(unittest.TestCase):
    """Tests for task code"""

    def test_func_vs_imp(self) -> None:
        """Confirms flexible action execution"""

        tf: BaseDecisionProcess[list[str]] = BaseDecisionProcess(lambda: ["hi"])

        self.assertEqual(tf.state, ["hi"])

        tf.add_action_factory(lambda _s, _io: [lambda s, _: s[1:]]).run_cycles()

        self.assertEqual(tf.state, [])

        #

        ti: BaseDecisionProcess[list[str]] = BaseDecisionProcess(lambda: ["hi"])

        self.assertEqual(ti.state, ["hi"])

        def a(s: list[str], _io: IOContainer) -> None:
            del s[0]

        ti.add_action_factory(lambda _s, _io: a).run_cycles()

        self.assertEqual(ti.state, [])

    def test_elab_dec(self) -> None:
        """Confirms elaborator decoration"""

        word = "test"
        t: BaseDecisionProcess[str] = BaseDecisionProcess(lambda: word)

        self.assertEqual(
            str(t),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        #

        e_name = "echo"

        @t.elaborator
        @stringify(e_name)
        def echo(s: str, _io: IOContainer) -> dict[str, Any]:
            return {e_name: s}

        self.assertEqual(
            str(t),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        #

        g_name = f"check_{e_name}"

        @t.termination_check
        @stringify(g_name)
        def check_echo(_s: str, io: IOContainer) -> bool:
            e_result = cast(
                str,
                getattr(
                    cast(
                        AttrReferral,
                        getattr(io.i, BaseDecisionProcess.SENSOR_ELABORATION),
                    ),
                    e_name,
                ),
            )

            return e_result == word

        self.assertEqual(
            str(t),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        t.run_until_done()

        self.assertEqual(
            str(t),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
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
        """Confirms some task basics"""

        a_inc = create_named_action("inc", lambda s, _io: s + 1)

        a_dec = create_named_action("dec", lambda s, _io: s - 1)

        ar_inc_low = ActionRank(a_inc, Rank.LOW)
        self.assertEqual(str(ar_inc_low), "ActionRank(a=inc, r=3)")

        ar_dec_high = ActionRank(a_dec, Rank.HIGH)
        self.assertEqual(str(ar_dec_high), "ActionRank(a=dec, r=1)")

        self.assertTrue(ar_dec_high < ar_inc_low)

        with self.assertRaises(TypeError):
            _ = ar_dec_high < "not an ActionRank"

        #

        starting_point: int = 100

        t: BaseDecisionProcess[int] = BaseDecisionProcess(lambda: starting_point)

        # no actions yet!
        with self.assertRaises(DecisionProcessExecutionError) as cm:
            for _ in t.phases():
                pass

        self.assertEqual(cm.exception.msg, DecisionProcessErrorMessage.NO_PROPOSAL)

        self.assertEqual(
            str(cm.exception), DecisionProcessErrorMessage.NO_PROPOSAL.value
        )

        t.reinit()

        #

        t.add_action_factory(lambda _s, _io: [a_inc, a_dec])

        # no evaluation of multiple possibilities
        with self.assertRaises(DecisionProcessExecutionError) as cm:
            for _ in t.cycles():
                pass

        self.assertEqual(cm.exception.msg, DecisionProcessErrorMessage.NO_RANK)

        self.assertEqual(str(cm.exception), DecisionProcessErrorMessage.NO_RANK.value)

        #

        t.add_action_evaluator(lambda _s, _io, _actions: [])

        #

        @t.action_evaluator
        def dec_over_inc(
            _s: int, _io: IOContainer, actions: Iterable[Action[int]]
        ) -> Iterable[ActionRank[int]]:
            """Always prefer dec over inc"""

            return [
                ar_inc_low if a == a_inc else ar_dec_high
                for a in actions
                if a in (a_dec, a_inc)
            ]

        t.run_cycles()

        self.assertEqual(t.state, starting_point - 1)
        self.assertEqual(t.num_cycles, 2)

        #

        t.add_termination_check(lambda s, _io: s == starting_point - 2)

        for _ in t.cycles():
            pass

        self.assertEqual(t.state, starting_point - 2)
        self.assertEqual(t.num_cycles, 3)

    def test_io(self) -> None:
        """Confirming basic io functionality"""

        starting_point: int = 1

        lst_name: str = "lst"
        lst: ListSensorActuator = ListSensorActuator()

        task_io: BaseDecisionProcess[int] = BaseDecisionProcess(lambda: starting_point)

        self.assertEqual(
            str(task_io),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        # add as both sensor/actuator
        task_io.set_sensor(lst_name, lst).set_actuator(lst_name, lst)

        # confirm registration
        self.assertEqual(
            str(task_io),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}, {lst_name}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}, {lst_name}",
                )
            ),
        )

        def inc_and_add_and_log(s: int, io: IOContainer) -> int:
            """
            * logs a combo of sensed data
            * adds sensed data to another actuator
            * progresses the task
            """

            sensed: str = str(cast(ListSensorActuator, getattr(io.i, lst_name)).data)
            cast(ListSensorActuator, getattr(io.o, lst_name)).add(str(s))

            log: StringIO = cast(
                StringIO, getattr(io.o, BaseDecisionProcess.ACTUATOR_LOG)
            )
            cycle: int = cast(
                TimeSensor[int], getattr(io.i, BaseDecisionProcess.SENSOR_TIME)
            ).cycles

            print(f"@{cycle}: data={sensed}", file=log)

            return s + 1

        a_name: str = "go"
        a_go = create_named_action(a_name, inc_and_add_and_log)

        factory_name: str = f"{a_name} factory"

        @stringify(factory_name)
        def go_action_factory(_s: int, _io: IOContainer) -> Action[int]:
            """always go!"""

            return a_go

        task_io.add_action_factory(go_action_factory)

        goal_diff: int = 3
        goal_name: str = f"{a_name} check {goal_diff}"

        @stringify(goal_name)
        def go_goal(s: int, _io: IOContainer) -> bool:
            """end after k increments"""

            return s == starting_point + goal_diff

        task_io.add_termination_check(go_goal).run_until_done()

        # confirm ability to remove sensors/actuators
        task_io.set_sensor(lst_name, None).set_actuator(lst_name, None)

        self.assertEqual(
            str(task_io),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        # confirm logging
        self.assertEqual(
            task_io.log,
            "\n".join(("@1: data=[]", "@2: data=['1']", "@3: data=['1', '2']", "")),
        )

    def test_count(self) -> None:
        """Confirming simple task execution"""

        starting_point: int = 1_001
        next_perfect_prime: int = 1_009

        e_prime: str = "prime"
        e_perfect: str = "perfect"
        a_inc: str = "inc"

        #

        task_count_until: BaseDecisionProcess[int] = (
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

        self.assertEqual(task_count_until.num_cycles, 0)

        self.assertEqual(task_count_until.state, starting_point)

        self.assertFalse(task_count_until.done)

        self.assertEqual(task_count_until.phase, Phase.ELABORATION)

        self.assertIsNone(task_count_until.chosen_action)

        self.assertEqual(
            str(task_count_until),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )

        task_count_until.run_until_done()

        self.assertEqual(task_count_until.num_cycles, 9)

        self.assertEqual(task_count_until.state, next_perfect_prime)

        self.assertTrue(task_count_until.done)

        self.assertEqual(task_count_until.phase, Phase.TERMINATIONCHECK)

        self.assertEqual(task_count_until.chosen_action, a_inc)

        self.assertEqual(
            str(task_count_until),
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
                        f"Sensors={BaseDecisionProcess.SENSOR_TIME}, "
                        f"{BaseDecisionProcess.SENSOR_ELABORATION}"
                    ),
                    f"Actuators={BaseDecisionProcess.ACTUATOR_LOG}",
                )
            ),
        )
