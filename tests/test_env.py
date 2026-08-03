"""
Tests for env code
"""

import unittest

from cognition import (
    Actuator,
    Environment,
    Sensor,
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

    def test_in_the_head(self) -> None:
        """tests non-environment"""

        self.assertListEqual(list(Environment.IN_THE_HEAD.sensors), [])
        self.assertListEqual(list(Environment.IN_THE_HEAD.actuators), [])

    def test_sensor_actuator(self) -> None:
        """tests s/a without env"""

        to_add1 = "howdy"
        to_add2 = "howdy"

        self.assertEqual(self.sensor.name, self.s_name)
        self.assertEqual(self.actuator.name, self.a_name)

        self.assertListEqual(list(self.sensor.sense()), [])

        self.assertEqual(self.actuator.actuate(to_add1), 1)
        self.assertListEqual(list(self.sensor.sense()), [to_add1])

        self.assertEqual(self.actuator.actuate(to_add2), 2)
        self.assertListEqual(list(self.sensor.sense()), [to_add1, to_add2])
