"""
Tests for env code
"""

import unittest

from cognition import (
    Actuator,
    BaseDecisionProcess,
    Sensor,
    create_actuator,
    create_sensor,
)

# ===


class ListSensor(Sensor[tuple[str, ...]]):
    """sensor access to a list"""

    def __init__(self, name: str, source: list[str]) -> None:
        self._name = name
        self._source = source

    @property
    def name(self) -> str:
        return self._name

    def sense(self) -> tuple[str, ...]:
        return tuple(self._source)


class ListAppender(Actuator[str, int]):
    """adds an element to a list"""

    def __init__(self, name: str, source: list[str]) -> None:
        self._name = name
        self._source = source

    @property
    def name(self) -> str:
        return self._name

    def actuate(self, param: str) -> int:
        self._source.append(param)
        return len(self._source)


# ===


class TestEnv(unittest.TestCase):
    """Tests for env code"""

    def setUp(self) -> None:

        self.shared_list: list[str] = []

        self.s_name = "looker"
        self.a_name = "appender"

        # ===

        self.sensor = ListSensor(self.s_name, self.shared_list)
        self.actuator = ListAppender(self.a_name, self.shared_list)

    def _test_sa(self, s: Sensor[tuple[str, ...]], a: Actuator[str, int]) -> None:
        """helper"""

        to_add1 = "howdy"
        to_add2 = "doody"

        self.assertEqual(s.name, self.s_name)
        self.assertEqual(a.name, self.a_name)

        self.assertListEqual(list(s.sense()), [])

        self.assertEqual(a.actuate(to_add1), 1)
        self.assertListEqual(list(s.sense()), [to_add1])

        self.assertEqual(a.actuate(to_add2), 2)
        self.assertListEqual(list(s.sense()), [to_add1, to_add2])

    def test_sensor_actuator(self) -> None:
        """tests s/a without env"""

        self._test_sa(self.sensor, self.actuator)

    def test_io(self) -> None:
        """tests s/a with manual dp"""

        to_add1 = "howdy"
        to_add2 = "doody"

        dp = BaseDecisionProcess(lambda: False)

        # ===

        with self.assertRaises(AttributeError):
            self.sensor.read(dp.io)

        with self.assertRaises(AttributeError):
            self.actuator.invoke(dp.io, to_add1)

        # ==

        self.actuator.install(dp)

        # ===

        self.sensor.perceive(dp)
        self.assertListEqual(list(self.sensor.read(dp.io)), [])

        self.assertEqual(self.actuator.invoke(dp.io, to_add1), 1)

        self.assertListEqual(list(self.sensor.read(dp.io)), [])
        self.sensor.perceive(dp)
        self.assertListEqual(list(self.sensor.read(dp.io)), [to_add1])
        self.assertListEqual(list(self.sensor.reader(dp.io)), [to_add1])

        self.assertEqual(self.actuator.invoker(dp.io, to_add2), 2)

        self.assertListEqual(list(self.sensor.read(dp.io)), [to_add1])
        self.sensor.perceive(dp)
        self.assertListEqual(list(self.sensor.read(dp.io)), [to_add1, to_add2])

    def test_dynamic(self) -> None:
        """test dynamic creation"""

        lst: list[str] = []

        def cp_list() -> tuple[str, ...]:
            return tuple(lst)

        def append_list(s: str) -> int:
            lst.append(s)
            return len(lst)

        # ===

        self._test_sa(
            create_sensor(self.s_name, cp_list),
            create_actuator(self.a_name, append_list),
        )

        # ===

        class MethodTest:
            """eg class"""

            def __init__(self) -> None:
                self._l: list[str] = []

            def cp(self) -> tuple[str, ...]:
                """tuple copy"""
                return tuple(self._l)

            def append(self, s: str) -> int:
                """append and return size"""

                self._l.append(s)
                return len(self._l)

        mt = MethodTest()

        self._test_sa(
            create_sensor(self.s_name, mt.cp),
            create_actuator(self.a_name, mt.append),
        )
