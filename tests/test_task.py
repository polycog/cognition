"""
Tests for task code
"""

from typing import Iterable, cast

from math import sqrt

import unittest

from io import StringIO

from cognition import (
    Action,
    ActionFactory,
    ActionRank,
    GoalCheck,
    IOContainer,
    Phase,
    Rank,
    Task,
    TaskExecutionError,
    TimeSensor,
    create_elaborator,
    create_named_action,
    stringify,
)

#

GOAL_NAME: str = "prime_or_perfect"
FACTORY_NAME: str = "always_inc"
ELAB_NAME: str = "prime_and_perfect"

def _make_goal(a_perfect: str, a_prime: str) -> GoalCheck[int]:
    """
    Create the perfect/prime goal check
    given the supplied elaboration
    attributes
    """

    @stringify(GOAL_NAME)
    def pred(_: int, io: IOContainer) -> bool:
        v_perfect = cast(
            bool,
            getattr(io.i.elaboration, a_perfect)
        )

        v_prime = cast(
            bool,
            getattr(io.i.elaboration, a_prime)
        )

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

    def test_basics(self) -> None:
        """Confirms some task basics"""

        a_inc = create_named_action(
            "inc",
            lambda s, _io: s + 1
        )

        a_dec = create_named_action(
            "dec",
            lambda s, _io: s - 1
        )

        ar_inc_low = ActionRank(a_inc, Rank.LOW)
        ar_dec_high = ActionRank(a_dec, Rank.HIGH)

        self.assertTrue(
            ar_dec_high < ar_inc_low
        )

        with self.assertRaises(TypeError):
            _ = ar_dec_high < "not an ActionRank"

        #

        starting_point: int = 100

        t: Task[int] = Task(lambda: starting_point)

        # no actions yet!
        with self.assertRaises(TaskExecutionError):
            for _ in t.phases():
                pass

        t.reinit()

        #

        t.add_action_factory(
            lambda _s, _io: [a_inc, a_dec]
        )

        # no evaluation of multiple possibilities
        with self.assertRaises(TaskExecutionError):
            for _ in t.cycles():
                pass

        #

        t.add_action_evaluator(
            lambda _s, _io, _actions: []
        )

        #

        def dec_over_inc(
                _s: int,
                _io: IOContainer,
                actions: Iterable[Action[int]]
        ) -> Iterable[ActionRank[int]]:
            """Always prefer dec over inc"""

            return [
                ar_inc_low if a == a_inc else ar_dec_high
                for a in actions
                if a in (a_dec, a_inc)
            ]

        t.add_action_evaluator(dec_over_inc)
        t.run_cycles()

        self.assertEqual(t.state, starting_point - 1)
        self.assertEqual(t.num_cycles, 2)

        #

        t.add_goal_check(
            lambda s, _io: s == starting_point - 2
        )

        for _ in t.cycles():
            pass

        self.assertEqual(t.state, starting_point - 2)
        self.assertEqual(t.num_cycles, 3)


    def test_io(self) -> None:
        """Confirming basic io functionality"""

        starting_point: int = 1

        lst_name: str = "lst"
        lst: ListSensorActuator = ListSensorActuator()

        task_io: Task[int] = Task(lambda: starting_point)

        self.assertEqual(
            str(task_io),
            "\n".join((
                f"Phase={Phase.ELABORATION.name}",
                f"State={starting_point}",
                f"Done?={False}",
                f"Chosen={None}",
                "Action Factories=",
                "Potential Actions=",
                "Action Evaluators=",
                "Rankings=",
                "Goal Checks=",
                "Elaborators=",
                f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                f"Actuators={Task.ACTUATOR_LOG}",
            ))
        )

        # add as both sensor/actuator
        task_io.set_sensor(lst_name, lst)
        task_io.set_actuator(lst_name, lst)

        # confirm registration
        self.assertEqual(
            str(task_io),
            "\n".join((
                f"Phase={Phase.ELABORATION.name}",
                f"State={starting_point}",
                f"Done?={False}",
                f"Chosen={None}",
                "Action Factories=",
                "Potential Actions=",
                "Action Evaluators=",
                "Rankings=",
                "Goal Checks=",
                "Elaborators=",
                f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}, {lst_name}",
                f"Actuators={Task.ACTUATOR_LOG}, {lst_name}",
            ))
        )

        def inc_and_add_and_log(s: int, io: IOContainer) -> int:
            """
            * logs a combo of sensed data
            * adds sensed data to another actuator
            * progresses the task
            """

            sensed: str = str(cast(ListSensorActuator, getattr(io.i, lst_name)).data)
            cast(ListSensorActuator, getattr(io.o, lst_name)).add(str(s))

            log: StringIO = cast(StringIO, getattr(io.o, Task.ACTUATOR_LOG))
            cycle: int = cast(TimeSensor[int], getattr(io.i, Task.SENSOR_TIME)).cycles

            print(f'@{cycle}: data={sensed}', file=log)

            return s + 1

        a_name: str = "go"
        a_go = create_named_action(
            a_name,
            inc_and_add_and_log
        )

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

        task_io.add_goal_check(go_goal)

        task_io.run_until_done()

        # confirm ability to remove sensors/actuators
        task_io.set_sensor(lst_name, None)
        task_io.set_actuator(lst_name, None)

        self.assertEqual(
            str(task_io),
            "\n".join((
                f"Phase={Phase.GOALCHECK.name}",
                f"State={starting_point + goal_diff}",
                f"Done?={True}",
                f"Chosen={a_name}",
                f"Action Factories={factory_name}",
                f"Potential Actions={a_name}",
                "Action Evaluators=",
                "Rankings=",
                f"Goal Checks={goal_name}",
                "Elaborators=",
                f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                f"Actuators={Task.ACTUATOR_LOG}",
            ))
        )

        # confirm logging
        self.assertEqual(
            task_io.log,
            "\n".join((
                "@1: data=[]",
                "@2: data=['1']",
                "@3: data=['1', '2']",
                ''
            ))
        )


    def test_count(self) -> None:
        """Confirming simple task execution"""

        starting_point: int = 1_001
        next_perfect_prime: int = 1_009

        e_prime: str = "prime"
        e_perfect: str = "perfect"
        a_inc: str = "inc"

        #

        task_count_until: Task[int] = Task(lambda: starting_point)
        task_count_until.add_goal_check(_make_goal(e_perfect, e_prime))
        task_count_until.add_elaborator(
            create_elaborator(
                ELAB_NAME,
                **{
                    e_prime: lambda s, _: _is_prime(s),
                    e_perfect: lambda s, _: sqrt(s) % 1 == 0,
                }
            )
        )
        task_count_until.add_action_factory(_make_increment_factory(a_inc))

        self.assertEqual(
            task_count_until.num_cycles,
            0
        )

        self.assertEqual(
            task_count_until.state,
            starting_point
        )

        self.assertFalse(
            task_count_until.done
        )

        self.assertEqual(
            task_count_until.phase,
            Phase.ELABORATION
        )

        self.assertIsNone(
            task_count_until.chosen_action
        )

        self.assertEqual(
            str(task_count_until),
            "\n".join((
                f"Phase={Phase.ELABORATION.name}",
                f"State={starting_point}",
                f"Done?={False}",
                f"Chosen={None}",
                f"Action Factories={FACTORY_NAME}",
                "Potential Actions=",
                "Action Evaluators=",
                "Rankings=",
                f"Goal Checks={GOAL_NAME}",
                f"Elaborators={ELAB_NAME}",
                f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                f"Actuators={Task.ACTUATOR_LOG}",
            ))
        )

        task_count_until.run_until_done()

        self.assertEqual(
            task_count_until.num_cycles,
            9
        )

        self.assertEqual(
            task_count_until.state,
            next_perfect_prime
        )

        self.assertTrue(
            task_count_until.done
        )

        self.assertEqual(
            task_count_until.phase,
            Phase.GOALCHECK
        )

        self.assertEqual(
            task_count_until.chosen_action,
            a_inc
        )

        self.assertEqual(
            str(task_count_until),
            "\n".join((
                f"Phase={Phase.GOALCHECK.name}",
                f"State={next_perfect_prime}",
                f"Done?={True}",
                f"Chosen={a_inc}",
                f"Action Factories={FACTORY_NAME}",
                f"Potential Actions={a_inc}",
                "Action Evaluators=",
                "Rankings=",
                f"Goal Checks={GOAL_NAME}",
                f"Elaborators={ELAB_NAME}",
                f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                f"Actuators={Task.ACTUATOR_LOG}",
            ))
        )
