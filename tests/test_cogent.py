"""
Tests for cogent code
"""

import unittest
from collections.abc import Iterable
from typing import Self

from cognition import (
    Actuator,
    Cogent,
    DecisionProcess,
    IOContainer,
    OperatorGenerator,
    PEState,
    Sensor,
    format_name_params,
    self_actuator,
    self_sensor,
    stringify,
    uniform_evaluator,
)

# ===


class SelfCogent(Cogent[str, DecisionProcess[str]]):
    """cogent with self sensor/actuator"""

    START_NUM: int = 42

    def __init__(self, decision_process: DecisionProcess[str]) -> None:
        super().__init__(decision_process)

        self._v = SelfCogent.START_NUM

    @self_sensor
    def get_val(self) -> int:
        """gets the hidden number"""

        return self._v

    @self_actuator
    def inc_val(self, amt: int) -> bool:
        """adds a value to the number, returning if it's positive"""

        self._v += amt

        return self._v > 0


class TestCogent(unittest.TestCase):
    """Tests for cogent code"""

    def setUp(self) -> None: ...

    def test_name(self) -> None:
        """tests cogent naming"""

        c_none = Cogent[int, DecisionProcess[int]](DecisionProcess(lambda: 0))

        self.assertEqual(c_none.name, Cogent.DEFAULT_NAME)
        self.assertDictEqual(dict(c_none.params), {})
        self.assertEqual(str(c_none), Cogent.DEFAULT_NAME)

        # ===

        name = "soar"
        c_name = Cogent[int, DecisionProcess[int]](DecisionProcess(lambda: 0), name)

        self.assertEqual(c_name.name, name)
        self.assertDictEqual(dict(c_name.params), {})
        self.assertEqual(str(c_name), name)

        # ===

        params = {"creator": "laird", "version": 9}

        c_combo = Cogent[int, DecisionProcess[int]](
            DecisionProcess(lambda: 0), name, **params
        )

        self.assertEqual(c_combo.name, name)
        self.assertDictEqual(dict(c_combo.params), params)
        self.assertEqual(str(c_combo), format_name_params(name, **params))

    def test_self(self) -> None:
        """tests s/a without env"""

        c = SelfCogent(DecisionProcess(lambda: ""))
        c.perceive()

        self.assertEqual(c.dp.io.i.get_val, SelfCogent.START_NUM)

        # ===

        to_add1 = 10

        self.assertTrue(c.dp.io.o.inc_val(to_add1))
        self.assertEqual(c.dp.io.i.get_val, SelfCogent.START_NUM)
        c.perceive()
        self.assertEqual(c.dp.io.i.get_val, SelfCogent.START_NUM + to_add1)

        # ===

        to_add2 = -(SelfCogent.START_NUM + to_add1 + 1)

        self.assertFalse(c.dp.io.o.inc_val(to_add2))
        self.assertEqual(c.dp.io.i.get_val, SelfCogent.START_NUM + to_add1)
        c.perceive()
        self.assertEqual(c.dp.io.i.get_val, SelfCogent.START_NUM + to_add1 + to_add2)

    def test_sensor_actuator(self) -> None:
        """tests s/a via classes"""

        c: Cogent[int, DecisionProcess[int]] = Cogent(DecisionProcess(lambda: 0))

        sa_name = "lst"
        lst: list[int] = []

        @c.sensor(lst=lst)
        class ListS(Sensor[str]):  # pylint: disable=unused-variable
            """eg sensor"""

            def __init__(self, lst: list[int]) -> None:
                self._lst: list[int] = lst

            @property
            def name(self) -> str:
                return sa_name

            def sense(self) -> str:
                return str(self._lst)

        @c.actuator(lst=lst)
        class ListA(Actuator[int, int]):  # pylint: disable=unused-variable
            """eg actuator"""

            def __init__(self, lst: list[int]) -> None:
                self._lst: list[int] = lst

            @property
            def name(self) -> str:
                return sa_name

            def actuate(self, param: int) -> int:
                self._lst.append(param)
                return len(self._lst)

        # ===

        c.perceive()

        self.assertEqual(c.dp.io.i.lst, "[]")

        # ===

        to_add = 51

        self.assertEqual(c.dp.io.o.lst(to_add), 1)
        self.assertEqual(c.dp.io.i.lst, "[]")
        c.perceive()
        self.assertEqual(c.dp.io.i.lst, f"[{to_add}]")

    def test_as(self) -> None:
        """tests s/a via funcs"""

        c: Cogent[int, DecisionProcess[int]] = Cogent(DecisionProcess(lambda: 0))

        lst: list[int] = []

        @c.as_sensor("foo")  # type: ignore
        def get() -> str:
            return str(lst)

        @c.as_actuator("bar")  # type: ignore
        def app(n: int) -> int:
            lst.append(n)
            return len(lst)

        c.perceive()

        self.assertEqual(c.dp.io.i.foo, "[]")

        # ===

        to_add = 51

        self.assertEqual(c.dp.io.o.bar(to_add), 1)
        self.assertEqual(c.dp.io.i.foo, "[]")
        c.perceive()
        self.assertEqual(c.dp.io.i.foo, f"[{to_add}]")

    def test_run(self) -> None:
        """cogent call"""

        type ClosedList = PEState[set[int]]

        init_set: set[int] = set()
        dp = DecisionProcess[ClosedList](PEState(init_set))
        dp.add_action_evaluator(uniform_evaluator(1, name="all_guesses_same"))

        c: Cogent[ClosedList, DecisionProcess[ClosedList]] = Cogent(dp)

        num_guesses: int = 0
        correct_val: int = 42
        upper_bound: int = 100
        got_it: bool = False

        @c.as_sensor("upper")  # type: ignore
        def upper() -> int:
            return upper_bound

        @c.as_actuator("guess")  # type: ignore
        def guess(param: int) -> bool:
            nonlocal num_guesses
            nonlocal got_it

            num_guesses += 1
            # print(f"tried: {param} ({num_guesses})")

            got_it = param == correct_val

            return got_it

        @c.dp.generator(None)
        class Guess(
            OperatorGenerator[ClosedList, None]
        ):  # pylint: disable=unused-variable
            """always guess!"""

            def __init__(self, num: int) -> None:
                super().__init__(num=num, terminal=True)
                self._num = num

            @classmethod
            def get_name(cls) -> str:
                return "guess"

            @classmethod
            def generate(
                cls, state: ClosedList, io: IOContainer, _extra: None
            ) -> Iterable[Self]:
                for n in range(io.i.upper):
                    if n not in state.p:
                        yield cls(n)

            def perform(self, state: ClosedList, io: IOContainer) -> None:
                state.p.add(self._num)
                io.o.guess(self._num)

        c(stringify("stop")(lambda _: False), 0)
        self.assertFalse(c.dp.done)
        self.assertFalse(got_it)
        self.assertEqual(num_guesses, len(c.dp.state.p))
        self.assertFalse(correct_val in c.dp.state.p)
        self.assertIsNone(c.dp.chosen_action)
        self.assertEqual(c.dp.num_cycles, 0)

        @stringify("keep_guessing")
        def keep_guessing(dp: DecisionProcess[ClosedList]) -> bool:
            return not correct_val in dp.state.p

        c(keep_guessing)

        self.assertTrue(c.dp.done)
        self.assertTrue(got_it)
        self.assertEqual(num_guesses, len(c.dp.state.p))
        self.assertTrue(correct_val in c.dp.state.p)
        self.assertEqual(
            c.dp.chosen_action, f"guess[num={correct_val}, terminal={True}]"
        )
        self.assertEqual(c.dp.num_cycles, 1)
