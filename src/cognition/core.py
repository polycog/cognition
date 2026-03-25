"""
PolyCog task orchestration
"""

from __future__ import annotations

from dataclasses import dataclass

from enum import IntEnum

from typing import (
    cast,
    Any,
    Iterable,
    Iterator,
    Optional,
)

from itertools import chain

from io import StringIO

import random

from cognition.utility import (
    AttrReferral,
    ImplementsLessThan,
)

from cognition.functypes import (
    BiConsumer,
    BiFunction,
    BiPredicate,
    Supplier,
    TriFunction,
)

#

@dataclass(frozen=True)
class IOContainer:
    """
    Convenience bundling of sensor/actuator access
    """

    i: AttrReferral
    o: AttrReferral


class Phase(IntEnum):
    """
    Representation of problem-solving phases
    """

    ELABORATION = 0
    GOALCHECK = 1
    PROPOSE = 2
    RANK = 3
    APPLY = 4


# An abstraction around monotonic reasoning
# based upon current state/io
type Elaborator[S] = BiFunction[S, IOContainer, dict[str, Any]]

# An abstraction around detecting task completion
type GoalCheck[S] = BiPredicate[S, IOContainer]

# An abstraction around potential change to state...
# - Consumer: support for mutable state
# - Function: support for replacing (immutable) state
type Action[S] = BiConsumer[S, IOContainer] | BiFunction[S, IOContainer, S]

# An abstraction around identifying viable actions
# in the present (supplied) state
type ActionFactory[S] = BiFunction[S, IOContainer, Action[S] | Iterable[Action[S]]]


@dataclass(frozen=True)
class ActionRank[S]:
    """Association of an action instance to a rank"""

    a: Action[S]
    rank: ImplementsLessThan

    def __lt__(self, other) -> bool:
        """
        Smaller rank values come first,
        with a deterministic ordering in
        ties facilitated by action string
        representations
        """

        if not isinstance(other, ActionRank):
            return NotImplemented

        return (self.rank < other.rank) or \
                ((self.rank == other.rank) and \
                 (str(self.a) < str(other.a)))


# An abstraction around producing relative rankings
# of a set of candidate actions (produced potentially
# from multiple sources)
type ActionEvaluator[S] = TriFunction[S, IOContainer, Iterable[Action[S]], Iterable[ActionRank[S]]]


class TaskExecutionError(Exception):
    """
    A custom exception related to invalid task execution
    """

    def __init__(self, msg: str) -> None:
        """Construct the error"""

        super().__init__(msg)


# pylint: disable=too-many-instance-attributes
class Task[S]:
    """
    Orchestration for a sequential decision-making problem
    """

    # Constants
    SENSOR_TIME: str = 'clock'
    SENSOR_TIME_ATTR: str = 'cycles'
    SENSOR_ELABORATION: str = 'elaboration'
    ACTUATOR_LOG: str = 'log'

    # Supplied components...
    _state: S  # arbitrary representation
    _state_init: Supplier[S]  # state start
    _elaborators: list[Elaborator[S]] # elaborates state each cycle
    _goal_checks: list[GoalCheck[S]]  # determines if the task been completed
    _action_factories: list[ActionFactory[S]]  # identifying potential next task steps
    _action_evaluators: list[ActionEvaluator[S]] = []  # ranking for supplied tasks

    # Internal task state...
    _goal_achieved: bool  # is the current task complete?
    _phase: Phase  # current phase of task operation
    _potential_actions: list[Action[S]]  # last computed set of potential actions
    _ranking: list[ActionRank[S]]  # last computed set of action ranking
    _chosen: Optional[Action[S]]  # last selected action
    _step_count: int  # number of task cycles since last initialization
    _elaboration: dict[str, Any]  # summary description of cycle state/io

    # Input/Output
    _sensors: dict[str, Any]
    _actuators: dict[str, Any]
    _io: IOContainer

    #

    def __init__(self, state_initializer: Supplier[S]) -> None:
        """
        Construct a new task
        """

        self._state_init = state_initializer
        self._elaborators = []
        self._goal_checks = []
        self._action_factories = []
        self._action_evaluators = []

        self._elaboration = {}

        self._sensors = {
            Task.SENSOR_TIME: TimeSensor(self),
            Task.SENSOR_ELABORATION: AttrReferral(self._elaboration)
        }
        self._actuators = {
            Task.ACTUATOR_LOG: StringIO()
        }
        self._io = IOContainer(
            AttrReferral(self._sensors),
            AttrReferral(self._actuators)
        )

        self.reinit()

    def reinit(self) -> None:
        """
        Restarts the task
        """
        self._state = self._state_init()

        self._goal_achieved = False
        self._phase = Phase.ELABORATION
        self._potential_actions = []
        self._ranking = []
        self._chosen = None
        self._step_count = 0
        self._elaboration.clear()

    def __str__(self) -> str:
        """
        Provides an extensive view of task internals
        """

        return "\n".join(
            f"{k}={v}"
            for k, v in {
                "Phase": f"{self.phase.name}",
                "State": str(self.state),
                "Done?": self.done,
                "Chosen": str(self._chosen),
                "Action Factories": ", ".join(str(f) for f in self._action_factories),
                "Potential Actions": ", ".join(str(a) for a in self._potential_actions),
                "Action Evaluators": ", ".join(
                    str(ae) for ae in self._action_evaluators
                ),
                "Rankings": ", ".join(str(ar) for ar in self._ranking),
                "Goal Checks": ", ".join(str(p) for p in self._goal_checks),
                "Elaborators": ", ".join(str(e) for e in self._elaborators),
                "Sensors": ", ".join(s for s in self._sensors),
                "Actuators": ", ".join(a for a in self._actuators),
            }.items()
        )

    @property
    def phase(self) -> Phase:
        """
        Current task phase
        """
        return self._phase

    @property
    def done(self) -> bool:
        """
        Has the task been completed?
        """
        return self._goal_achieved

    @property
    def state(self) -> S:
        """
        Current task state
        """
        return self._state

    @property
    def num_cycles(self) -> int:
        """
        Indicates how many task cycles have occurred
        since last initialization
        """
        return self._step_count

    @property
    def chosen_action(self) -> Optional[str]:
        """
        String representation of the most
        recently chosen action
        """
        return None if self._chosen is None else str(self._chosen)

    #

    def add_elaborator(self, e: Elaborator[S]) -> None:
        """
        Add a reasoner to add context to the state/io representation
        """

        self._elaborators.append(e)

    def _elaborate(self) -> None:
        """
        Elaboration phase: allows an opportunity to perform monotonic
                           reasoning over state
        """

        if self._phase == Phase.ELABORATION:
            self._elaboration.clear()

            for e in self._elaborators:
                self._elaboration |= e(self._state, self._io)

            self._phase = Phase.GOALCHECK

    #

    def add_goal_check(self, p: GoalCheck[S]) -> None:
        """
        Add a task-predicate to identify a cause of task completion
        """

        self._goal_checks.append(p)

    def _goal_check(self) -> None:
        """
        GoalCheck phase: task is complete if any goal check returns True
                         (and if so shifts to Propose phase)
        """
        if (not self._goal_achieved) and (self._phase == Phase.GOALCHECK):
            self._step_count += 1
            self._goal_achieved = any(p(self._state, self._io) for p in self._goal_checks)

            if not self._goal_achieved:
                self._phase = Phase.PROPOSE

    #

    def add_action_factory(self, f: ActionFactory[S]) -> None:
        """
        Adds a factory to propose potential action(s) given current state
        """

        self._action_factories.append(f)

    @staticmethod
    def _make_iterable(
        proposal: Action[S] | Iterable[Action[S]]
    ) -> Iterable[Action[S]]:
        """
        Helps unify processing of either
        one or more actions
        """

        if hasattr(proposal, "__iter__"):
            return proposal

        return (proposal,)

    def _propose(self) -> None:
        """
        Propose phase: allow factories to produce candidate actions
                       (and then shift to Rank phase)
        """
        if self._phase == Phase.PROPOSE:
            self._potential_actions = list(
                chain.from_iterable(
                    Task._make_iterable(f(self._state, self._io))
                    for f in self._action_factories
                )
            )
            self._phase = Phase.RANK

    #

    def add_action_evaluator(self, ae: ActionEvaluator[S]) -> None:
        """
        Adds an evaluator of potential actions
        """

        self._action_evaluators.append(ae)

    def _rank(self) -> None:
        """
        Rank phase: allow evaluators to produce action rankings
                    and then select one from amongst the best
                    ranking (and then shift to Apply phase)
        """
        if self._phase == Phase.RANK:
            self._chosen = None

            if self._potential_actions:
                self._ranking = []

                if len(self._potential_actions) > 1:
                    self._ranking = list(
                        sorted(
                            chain.from_iterable(
                                ae(self._state, self._io, self._potential_actions)
                                for ae in self._action_evaluators
                            )
                        )
                    )

                    if len(self._ranking) == 0:
                        raise TaskExecutionError("No action rankings")

                    top = list(
                        filter(
                            lambda r: r.rank == self._ranking[0].rank,
                            self._ranking
                        )
                    )
                    self._chosen = random.sample(top, k=1)[0].a
                else:
                    self._chosen = self._potential_actions[0]

                self._phase = Phase.APPLY
            else:
                raise TaskExecutionError("No potential actions")

    #

    def _apply(self) -> None:
        """
        Apply phase: executes the selected action (if one exists);
                     state is...
                     * replaced if action produces a result
                     * unchanged by the Task otherwise (assumed
                       to have been modified in-place by the
                       action itself)
        """
        if self._phase == Phase.APPLY:
            if self._chosen:
                result: Optional[S] = self._chosen(self._state, self._io)
                if result:
                    self._state = result

                self._phase = Phase.ELABORATION
            else:
                raise TaskExecutionError("No chosen action")

    #

    def run_phase(self) -> None:
        """
        Executes the current task phase
        """

        match self.phase:
            case Phase.ELABORATION:
                self._elaborate()

            case Phase.GOALCHECK:
                self._goal_check()

            case Phase.PROPOSE:
                self._propose()

            case Phase.RANK:
                self._rank()

            case Phase.APPLY:
                self._apply()

    def run_cycles(self, n: int = 1) -> None:
        """
        Executes n cycles of the full task-phases
        """

        for _ in range(n):
            for _ in range(len(Phase)):
                self.run_phase()

    def run_until_done(self) -> None:
        """
        Runs until task completion
        """

        while not self.done:
            self.run_phase()

    #

    def phases(self) -> Iterator[Task[S]]:
        """
        Convenience function to support task
        iteration by phase
        """

        return TaskIterator(self, True)

    def cycles(self) -> Iterator[Task[S]]:
        """
        Convenience function to support task
        iteration by cycle
        """

        return TaskIterator(self, False)

    #

    @staticmethod
    def _set_io_buffer(d: dict[str, Any], name: str, buffer: Any) -> None:
        """Abstraction for sensor/actuator setting"""

        if buffer is None:
            if name in d:
                del d[name]
        else:
            d[name] = buffer

    def set_sensor(self, name: str, buffer: Any) -> None:
        """
        Associates a sensor name with an
        object reference (overriding any
        previous association); None
        removes the sensor's name.
        """

        Task._set_io_buffer(self._sensors, name, buffer)

    def set_actuator(self, name: str, buffer: Any) -> None:
        """
        Associates an actuator name with an
        object reference (overriding any
        previous association); None
        removes the actuator's name.
        """

        Task._set_io_buffer(self._actuators, name, buffer)

    @property
    def log(self) -> str:
        """
        Retrieves the result of any logging actuation
        """

        logger: StringIO = cast(StringIO, self._actuators[Task.ACTUATOR_LOG])
        return logger.getvalue()


# pylint: disable=too-few-public-methods
class TimeSensor[S]:
    """
    Sensor implementation to provide access
    to the current cycle count within a task.
    """

    def __init__(self, t: Task[S]):
        self._t: Task[S] = t

    @property
    def cycles(self) -> int:
        """
        Gets associated task's cycle count
        """

        return self._t.num_cycles

# pylint: disable=too-few-public-methods
class TaskIterator[S](Iterator[Task[S]]):
    """
    Custom iterator to facilitate easy task iteration
    via either phase or cycle
    """

    def __init__(self, t: Task[S], by_phase: bool = True) -> None:
        """
        Constructs an iterator for a task either
        by phase or cycle
        """

        self._task: Task[S] = t
        self._by_phase: bool = by_phase

    def __next__(self) -> Task[S]:
        """
        Provides the next phase/cycle
        if the task is not complete
        """

        if self._task.done:
            raise StopIteration

        if self._by_phase:
            self._task.run_phase()
        else:
            self._task.run_cycles()

        return self._task
