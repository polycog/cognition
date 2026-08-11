"""
Model of the choice environment
"""

from dataclasses import asdict, dataclass
from typing import Any, override

from cognition import Actuator, ActuatorInvoker, Cogent, Sensor, SensorReader

from container import ChoiceContainer

# ===


@dataclass(frozen=True)
class FieldChoice:
    """
    Data type produced for field options sensing
    """

    options: tuple[str, ...]


class FieldSensor(Sensor[FieldChoice]):
    """
    Exposes set of fields
    """

    def __init__(self, container: ChoiceContainer) -> None:
        """
        :param container: source choice context
        """

        self._fc = FieldChoice(tuple(container.field_names))

    @override
    def sense(self) -> FieldChoice:
        return self._fc

    @override
    @property
    def name(self) -> str:
        return "fields"


# ===


@dataclass(frozen=True)
class FieldValueChoice:
    """
    Data type produced for field value sensing
    """

    name: str
    options: tuple[str, ...]
    choice: str | None


class FieldValueSensorActuator(Sensor[FieldValueChoice], Actuator[str, bool]):
    """
    Ability for an agent to get the status of
    and make a choice about a field value
    """

    @staticmethod
    def naming(field_name: str) -> str:
        """
        Naming pattern for an instance

        :param field_name: choice field
        :return: how to name based upon the field
        """

        return f"choice_{field_name}"

    # ===

    def __init__(self, container: ChoiceContainer, field_name: str) -> None:
        """
        :param container: source choice context
        :param field_name: target field for this instance
        """

        self._c = container
        self._f = field_name
        self._t = container.choice_type(field_name)
        self._opts = tuple(member.name for member in self._t)
        self._name = type(self).naming(field_name)

    @override
    @property
    def name(self) -> str:
        return self._name

    @override
    def sense(self) -> FieldValueChoice:
        current_value = asdict(self._c)[self._f]

        return FieldValueChoice(
            self._f, self._opts, current_value.name if current_value else None
        )

    @override
    def actuate(self, param: str) -> bool:
        if param in self._opts:
            setattr(self._c, self._f, self._t[param])
            return True

        return False


# ===


class ChoiceEnvironment[T: ChoiceContainer]:
    """
    Organizational unit for the sensors
    and actuators associated with a
    particular choice container
    """

    def __init__(self, container: T) -> None:
        """
        :param container: source choice context
        """

        self._c = container
        self._f_s = FieldSensor(container)
        self._fv_sa = {
            f: FieldValueSensorActuator(container, f) for f in container.field_names
        }

    @property
    def container(self) -> T:
        """
        :return: the referenced choice container
        """

        return self._c

    def reader(self, field_name: str) -> SensorReader[FieldValueChoice]:
        """
        Access to sensor reader for a field

        :param field_name: field for which to produce a reader
        :return: sensor reader
        """

        return self._fv_sa[field_name].reader

    def invoker(self, field_name: str) -> ActuatorInvoker[str, bool]:
        """
        Access to actuator invoker for a field

        :param field_name: field for which to produce an invoker
        :return: actuator invoker
        """

        return self._fv_sa[field_name].invoker

    @property
    def fields_reader(self) -> SensorReader[FieldChoice]:
        """
        Access to the sensor reader for available fields

        :return: sensor reader
        """

        return self._f_s.reader

    def add_sensors_actuators(self, c: Cogent[Any]) -> None:
        """
        :param c: target cogent
        """

        c.add_sensor(self._f_s)

        for sa in self._fv_sa.values():
            c.add_sensor(sa).add_actuator(sa)
