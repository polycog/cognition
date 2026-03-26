"""
Tests for task code
"""

from math import sqrt

import unittest

from cognition import (
    Action,
    ActionFactory,
    GoalCheck,
    IOContainer,
    Phase,
    Task,
    create_elaborator,
    stringify,
)

#

GOAL_NAME: str = "prime_or_perfect"
FACTORY_NAME: str = "always_inc"
ELAB_NAME: str = "prime_and_perfect"

def make_goal(a_perfect: str, a_prime: str) -> GoalCheck[int]:
    """
    Create the perfect/prime goal check
    given the supplied elaboration
    attributes
    """

    @stringify(GOAL_NAME)
    def pred(_: int, io: IOContainer) -> bool:
        return getattr(io.i.elaboration, a_perfect) or \
                getattr(io.i.elaboration, a_prime)

    return pred


def is_prime(number: int) -> bool:
    """
    Determines if a supplied integer is prime (slowly)
    """
    if number <= 1:
        return False

    for i in range(2, int(sqrt(number)) + 1):
        if number % i == 0:
            return False

    return True


def make_increment_factory(a_name: str) -> ActionFactory[int]:
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


class TestTask(unittest.TestCase):
    """Tests for task code"""

    def test_count(self) -> None:
        """Confirming simple task execution"""

        starting_point: int = 1_001
        next_perfect_prime: int = 1_009

        e_prime: str = "prime"
        e_perfect: str = "perfect"
        a_inc: str = "inc"

        #

        task_count_until: Task[int] = Task(lambda: starting_point)
        task_count_until.add_goal_check(make_goal(e_perfect, e_prime))
        task_count_until.add_elaborator(
            create_elaborator(
                ELAB_NAME,
                **{
                    e_prime: lambda s, _: is_prime(s),
                    e_perfect: lambda s, _: sqrt(s) % 1 == 0,
                }
            )
        )
        task_count_until.add_action_factory(make_increment_factory(a_inc))

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
