"""
Environments
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol, cast, final

from ..decision.core import BaseDecisionProcess, IOContainer
from ..util.functypes import BiFunction, Function, Supplier
from ..util.misc import stringify

# ===

_logger = logging.getLogger(__name__)

# ===


# pylint: disable=too-few-public-methods
class BaseSensor[T](Protocol):
    """
    Base interface for external input (of
    type ``T``) to a cogent
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


def perceive[ST](sensor: BaseSensor[ST], dp: BaseDecisionProcess[Any]) -> None:
    """
    Route sensing for a single time point to
    the IOContainer of a decision process.

    :param sensor: source sensor
    :param dp: destination decision process
    """

    _logger.info("Sensor perception to decision process: %s", sensor.name)

    new_val = sensor.sense()

    _logger.debug(new_val)

    dp.set_input_data(sensor.name, sensor.sense())


def read_sensor_data[ST](sensor: BaseSensor[ST], io: IOContainer) -> ST:
    """
    Retrieve sensed data from io cache.

    :param sensor: source sensor
    :param io: io cache
    :return: most recent sensed data
    """

    return cast(ST, getattr(io.i, sensor.name))


type SensorReader[T] = Function[IOContainer, T]
"""Represents a function to extract a sensor type from an io container"""


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

    @final
    @property
    def reader(self) -> SensorReader[T]:
        """
        Produces an easy-to-call function to
        extract sensor data from an io container

        :return: associated sensor reader
        """

        return self.read


def create_sensor[ST](name: str, sense_f: Supplier[ST]) -> Sensor[ST]:
    """
    Dynamically constructs a sensor instance.

    :param name: sensor name
    :param sense_f: function to produce input data
    :return: sensor
    """

    class DynamicSensor(Sensor[ST]):
        """new subclass"""

        @property
        def name(self) -> str:
            return name

        def sense(self) -> ST:
            return sense_f()

    return DynamicSensor()


# pylint: disable=too-few-public-methods
class BaseActuator[P, F](Protocol):
    """
    Base interface for external output from
    a cogent; actuation is parameterized via
    type ``P`` and result feeback via ``F``
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


def install[AP, AF](
    actuator: BaseActuator[AP, AF], dp: BaseDecisionProcess[Any]
) -> None:
    """
    Provide persistent access to the actuator
    via the IOContainer of the decision process

    :param actuator: actuator to install
    :param dp: destination decision process
    """

    _logger.info("Actuator installed in decision process: %s", actuator.name)

    dp.set_output_channel(
        actuator.name,
        stringify(f"Actuator[name={actuator.name}, cls={type(actuator).__name__}]")(
            actuator.actuate
        ),
    )


def invoke_actuator[AP, AF](
    actuator: BaseActuator[AP, AF], io: IOContainer, param: AP
) -> AF:
    """
    Invokes an actuator via io.

    :param actuator: actuator to invoke
    :param io: io container
    :param param: input to the actuator
    :return: actuator feedback from invocation
    """

    return cast(AF, getattr(io.o, actuator.name)(param))


type ActuatorInvoker[P, F] = BiFunction[IOContainer, P, F]
"""Represents a function to invoke an actuator on an io container"""


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

    @final
    @property
    def invoker(self) -> ActuatorInvoker[P, F]:
        """
        Produces an easy-to-call function to
        invoke an actuator on an io container

        :return: associated sensor reader
        """

        return self.invoke


def create_actuator[AP, AF](name: str, actuate_f: Function[AP, AF]) -> Actuator[AP, AF]:
    """
    Dynamically constructs an actuator instance.

    :param name: actuator name
    :param sense_f: function to handle actuation
    :return: actuator
    """

    class DynamicActuator(Actuator[AP, AF]):
        """new subclass"""

        @property
        def name(self) -> str:
            return name

        def actuate(self, param: AP) -> AF:
            return actuate_f(param)

    return DynamicActuator()
