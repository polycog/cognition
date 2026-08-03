"""
Environments
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any, Protocol, cast, final, override

from ..decision.core import BaseDecisionProcess, IOContainer

# ===


# pylint: disable=too-few-public-methods
class SensorReader[T](Protocol):
    """
    Interface to facilitate typed sensor
    access from IO - preferred for cogents.
    """

    def read(self, io: IOContainer) -> T:
        """
        Reads the current sensor input

        :param io: reference to IO
        :return: current value for associated sensor
        """


class Sensor[T](ABC, SensorReader[T]):
    """
    Base interface for external input (of
    type `T`) to an environment
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Sensor name, which corresponds to access
        location on io: IOContainer.i.<name>

        :return: this sensor's name
        """

    @abstractmethod
    def sense(self) -> T:
        """
        Retrieve the current sensor value.

        Generally this should not be called
        directly, but rather synchronized
        via perception across all sensors,
        and then cached within the IOContainer.

        :return: current sensor value
        """

    def perceive(self, dp: BaseDecisionProcess[Any]) -> None:
        """
        Integrates the sensing for a single time point
        within a decision process.

        Generally this should not be called reictly,
        but rather synchronized via perception across
        all sensors.

        :param dp: decision process
        """

        dp.set_sensor(self.name, self.sense())

    @override
    @final
    def read(self, io: IOContainer) -> T:
        """
        Default reader implementation.

        :param io: access to IO
        :return: this sensor's value from IO
        """
        return cast(T, getattr(io.i, self.name))

    @final
    @property
    def reader(self) -> SensorReader[T]:
        """
        IOContainer reading for this sensor.

        :return: an IOContainer reader for this sensor
        """

        return self


# pylint: disable=too-few-public-methods
class ActuatorWriter[I, O](Protocol):
    """
    Interface to facilitate typed actuation
    access via IO - preferred for cogents.
    """

    def write(self, io: IOContainer, param: I) -> O:
        """
        Performs actuation

        :param io: reference to IO
        :param param: typed input to the actuator
        :return: typed response from actuation
        """


class Actuator[I, O](ABC, ActuatorWriter[I, O]):
    """
    Base interface for external output to an environment;
    actuation is parameterized via type `I` and
    provides feedback via type `O`
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Actuator name, which corresponds to access
        location on io: IOContainer.o.<name>

        :return: this actuator's name
        """

    @abstractmethod
    def actuate(self, param: I) -> O:
        """
        Function exposed via IOContainer

        :param param: typed input
        :return: typed actuator response
        """

    def install(self, dp: BaseDecisionProcess[Any]) -> None:
        """
        Integrates this actuator within a decision process

        :param dp: decision process
        """

        dp.set_actuator(self.name, self.actuate)

    @override
    @final
    def write(self, io: IOContainer, param: I) -> O:
        """
        Default writer implementation.

        :param io: access to IO
        :param param: input to send to the actuator
        :return: this actuator's response
        """

        return cast(O, getattr(io.o, self.name)(param))

    @final
    @property
    def writer(self) -> ActuatorWriter[I, O]:
        """
        IOContainer writing for this actuator.

        :return: an IOContainer writer for this actuator
        """

        return self


class Environment(Protocol):
    """what's needed for an environment"""

    IN_THE_HEAD: Environment = SimpleNamespace(
        name="InTheHead",
        sensors=(),
        actuators=(),
    )
    """Constant for an environment with no external sensing/acutation"""

    @property
    def sensors(self) -> Iterable[Sensor[Any]]:
        """
        :return: this environment's sensor(s)
        """

    @property
    def actuators(self) -> Iterable[Actuator[Any, Any]]:
        """
        :return: this environment's actuator(s)
        """
