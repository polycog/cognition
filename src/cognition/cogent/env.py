"""
Environments
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, cast, final

from ..decision.core import BaseDecisionProcess, IOContainer

# ===


# pylint: disable=too-few-public-methods
class BaseSensor[T](Protocol):
    """
    Base interface for external input (of
    type `T`) to a cogent
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

        Generally this should NOT be called
        directly, but rather synchronized
        via perception across all sensors,
        in an agent (where results are
        cached within an IOContainer).

        :return: current sensor value
        """


def perceive[T](sensor: BaseSensor[T], dp: BaseDecisionProcess[Any]) -> None:
    """
    Route sensing for a single time point to
    the IOContainer of a decision process.

    :param sensor: source sensor
    :param dp: destination decision process
    """

    dp.set_input_data(sensor.name, sensor.sense())


def read_sensor_data[T](sensor: BaseSensor[T], io: IOContainer) -> T:
    """
    Retrieve sensed data from io cache.

    :param sensor: source sensor
    :param io: io cache
    :return: most recent sensed data
    """

    return cast(T, getattr(io.i, sensor.name))


class Sensor[T](ABC, BaseSensor[T]):
    """
    Useful implementation of a sensor
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def sense(self) -> T: ...

    @final
    def perceive(self, dp: BaseDecisionProcess[Any]) -> None:
        """
        See :func:`perceive`
        """

        perceive(self, dp)

    @final
    def read(self, io: IOContainer) -> T:
        """
        See :func:`read_sensor_data`
        """

        return read_sensor_data(self, io)


# pylint: disable=too-few-public-methods
class BaseActuator[P, F](Protocol):
    """
    Base interface for external output from
    a cogent; actuation is parameterized via
    type `P` and result feeback via `F`
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
    def actuate(self, param: P) -> F:
        """
        Function exposed via IOContainer to
        invoke the actuator and receive feedback

        :param param: typed parameter
        :return: typed actuator feedback
        """


def install[P, F](actuator: BaseActuator[P, F], dp: BaseDecisionProcess[Any]) -> None:
    """
    Provide persistent access to the actuator
    via the IOContainer of the decision process

    :param actuator: actuator to install
    :param dp: destination decision process
    """

    dp.set_output_channel(actuator.name, actuator.actuate)


def invoke_actuator[P, F](actuator: BaseActuator[P, F], io: IOContainer, param: P) -> F:
    """
    Invokes an actuator via io.

    :param actuator: actuator to invoke
    :param io: io container
    :param param: input to the actuator
    :return: actuator feedback from invocation
    """

    return cast(F, getattr(io.o, actuator.name)(param))


class Actuator[P, F](ABC, BaseActuator[P, F]):
    """
    Useful implementation of an actuator
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def actuate(self, param: P) -> F: ...

    @final
    def install(self, dp: BaseDecisionProcess[Any]) -> None:
        """
        See :func:`install`
        """

        install(self, dp)

    @final
    def invoke(self, io: IOContainer, param: P) -> F:
        """
        See :func:`invoke_actuator`
        """

        return invoke_actuator(self, io, param)
