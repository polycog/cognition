"""
(Cog)nitive ag(ents)
"""

from typing import Any, Self

from ..decision.core import BaseDecisionProcess
from ..decision.dp import args_added
from ..util.functypes import BiFunction, Function, Predicate, Supplier
from .env import (
    BaseActuator,
    BaseSensor,
    create_actuator,
    create_sensor,
    install,
    perceive,
)

# ===


def self_sensor[C: Cogent[Any, Any], T](m: Function[C, T]) -> Function[C, T]:
    """
    Decorator to mark a cogent method for use as a sensor upon instance init

    :param f: method
    """

    # pylint: disable=protected-access
    m._is_selfsensor = True  # type: ignore[attr-defined]
    return m


def self_actuator[C: Cogent[Any, Any], P, F](
    m: BiFunction[C, P, F],
) -> BiFunction[C, P, F]:
    """
    Decorator to mark a cogent method for use as an actuator upon instance init

    :param f: method
    """

    # pylint: disable=protected-access
    m._is_selfactuator = True  # type: ignore[attr-defined]
    return m


class Cogent[S, DP: BaseDecisionProcess[S]]:  # type: ignore[name-defined]
    """
    Base for a cognitive agent
    """

    _self_sensors: dict[str, Function["Cogent[S, DP]", Any]]
    _self_actuators: dict[str, BiFunction["Cogent[S, DP]", Any, Any]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        cls._self_sensors = {
            name: val
            for name, val in vars(cls).items()
            if callable(val) and getattr(val, "_is_selfsensor", False)
        }

        cls._self_actuators = {
            name: val
            for name, val in vars(cls).items()
            if callable(val) and getattr(val, "_is_selfactuator", False)
        }

    def _add_self_tagged(self) -> None:

        if hasattr(self, "_self_sensors"):
            for s_n, s_m in self._self_sensors.items():

                def _self_sensor[T](orig_method: Function[Cogent[S, DP], T] = s_m) -> T:
                    return orig_method(self)

                self.add_sensor(create_sensor(s_n, _self_sensor))

        if hasattr(self, "_self_actuators"):
            for a_n, a_m in self._self_actuators.items():

                def _self_actuator[P, F](
                    param: P, orig_method: BiFunction[Cogent[S, DP], P, F] = a_m
                ) -> F:
                    return orig_method(self, param)

                self.add_actuator(create_actuator(a_n, _self_actuator))

    # ===

    def __init__(self, decision_process: DP) -> None:
        """
        :param decision_process: agent control
        """

        self._dp = decision_process
        self._sensors: set[BaseSensor[Any]] = set()

        # ===

        self._add_self_tagged()

    @property
    def dp(self) -> DP:
        """
        :return: decision process for this cogent
        """

        return self._dp

    def add_sensor(self, sensor: BaseSensor[Any]) -> Self:
        """
        Add a sensor to the cogent

        :param sensor: sensor to add
        :return: this cogent (for chaining)
        """

        self._sensors.add(sensor)
        return self

    def sensor(
        self,
        **kwargs: Any,
    ) -> Function[type[BaseSensor[Any]], type[BaseSensor[Any]]]:
        """
        Decorator version of :meth:`Cogent.add_sensor`

        :param kwargs: instantiation argument(s)
        :return: parameterized decorator
        """

        def cls_dec(cls: type[BaseSensor[Any]]) -> type[BaseSensor[Any]]:
            """
            Adds a sensor instance to this cogent.

            :param cls: sensor to instantiate
            :return: added class
            """

            self.add_sensor(cls(**kwargs))
            return cls

        return cls_dec

    def as_sensor[T](self, name: str) -> Function[Supplier[T], Supplier[T]]:
        """
        Decorator version of :func:`create_sensor`

        :param name: name for the sensor instance
        :return: parameterized decorator
        """

        def dec(f: Supplier[T]) -> Supplier[T]:
            self.add_sensor(create_sensor(name, f))
            return f

        return dec

    def add_actuator(self, actuator: BaseActuator[Any, Any]) -> Self:
        """
        Add an actuator to the cogent

        :param actuator: actuator to add
        :return: this cogent (for chaining)
        """

        install(actuator, self._dp)
        return self

    def actuator(
        self,
        **kwargs: Any,
    ) -> Function[type[BaseActuator[Any, Any]], type[BaseActuator[Any, Any]]]:
        """
        Decorator version of :meth:`Cogent.add_actuator`

        :param kwargs: instantiation argument(s)
        :return: parameterized decorator
        """

        def cls_dec(cls: type[BaseActuator[Any, Any]]) -> type[BaseActuator[Any, Any]]:
            """
            Adds a actuator instance to this cogent.

            :param cls: actuator to instantiate
            :return: added class
            """

            self.add_actuator(cls(**kwargs))
            return cls

        return cls_dec

    def as_actuator[P, F](self, name: str) -> Function[Function[P, F], Function[P, F]]:
        """
        Decorator version of :func:`create_actuator`

        :param name: name for the actuator instance
        :return: parameterized decorator
        """

        def dec(f: Function[P, F]) -> Function[P, F]:
            self.add_actuator(create_actuator(name, f))
            return f

        return dec

    def perceive(self) -> None:
        """
        All added sensors are routed to the decision process IO container
        """

        for s in self._sensors:
            perceive(s, self._dp)

    def __call__(
        self, repeat_p: Predicate[DP], max_cycles: int | None = None, **args: Any
    ) -> Self:
        """
        Runs a cogent loop...

        1. Reinitialize the decision process
        2. Augment io with supplied arguments
        3. Cache sensor(s) perception to IO
        4. Run the decision process

        until the supplied gating predicate returns `False`

        :param repeat_p: gating predicate
        :param max_cycles: maximum dp cycles to run per loop;
                           `None` indicates no limit
        :param args: IO args to add (see :func:`args_added`)
        """

        proceed = True
        self._dp.reinit()

        with args_added(self._dp, **args):
            while proceed:
                self.perceive()
                if max_cycles is None:
                    self._dp.run_until_done()
                else:
                    self._dp.run_cycles(max_cycles)

                proceed = repeat_p(self._dp)
                if proceed:
                    self._dp.reinit()

        return self
