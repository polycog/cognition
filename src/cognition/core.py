"""
Task orchestration
"""

from __future__ import annotations

from dataclasses import dataclass

from enum import IntEnum, StrEnum

from typing import (
    cast,
    Any,
    Optional,
)

from collections.abc import (
    Iterable,
    Iterator,
)

from itertools import chain

from io import StringIO

import random

from .utility import (
    AttrReferral,
    ImplementsLessThan,
    stringify,
)

from .functypes import (
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
    """Access to (i)nput via sensors"""

    o: AttrReferral
    """Access to (o)utput via actuators"""


class Phase(IntEnum):
    """
    Representation of task phases
    """

    ELABORATION = 0
    """Monotonic summarization of state"""

    GOALCHECK = 1
    """Detect task completion"""

    PROPOSE = 2
    """Factories to produce candidate actions"""

    RANK = 3
    """Select an action (via evaluator action rankings)"""

    APPLY = 4
    """Execute the selected action"""

    @property
    def next(self) -> Phase:
        """
        Cyclic enumeration

        :return: next phase
        """

        return Phase((self + 1) % len(Phase))


type Elaborator[S] = BiFunction[S, IOContainer, dict[str, Any]]
"""Monotonically summarizes current state"""

type GoalCheck[S] = BiPredicate[S, IOContainer]
"""Detects task completion based upon current state"""

type Action[S] = BiFunction[S, IOContainer, S | None]
"""Changes state via mutation (return None) or replacement (return ``S``)"""

type ActionFactory[S] = BiFunction[S, IOContainer, Action[S] | Iterable[Action[S]]]
"""Identifies viable actions in the current state"""


@dataclass(frozen=True)
class ActionRank[S]:
    """Pairs an action and rank"""

    a: Action[S]
    """Action"""

    rank: ImplementsLessThan
    """Rank of the action (smaller is better)"""

    def __str__(self) -> str:
        return (
            "ActionRank("
            f"a={str(self.a)}, "
            f"r={str(self.rank)}"
            ")"
        )

    def __lt__(self, other: object) -> bool:
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


type ActionEvaluator[S] = TriFunction[S, IOContainer, Iterable[Action[S]], Iterable[ActionRank[S]]]
"""Produces rankings of candidate actions"""


class TaskErrorMessage(StrEnum):
    """
    Known errors with messages
    """

    NO_PROPOSAL = "No potential actions"
    """No candidate actions produced from factories"""

    NO_RANK = "No action rankings"
    """No rankings produced (given multiple candidate actions)"""

    NO_CHOICE = "No chosen action"
    """No action chosen to apply (should not occur)"""

class TaskExecutionError(Exception):
    """
    A custom exception related to invalid task execution

    :param msg: task error message
    """

    def __init__(self, msg: TaskErrorMessage) -> None:
        super().__init__(msg.value)
        self._msg = msg

    @property
    def msg(self) -> TaskErrorMessage:
        """
        :return: task error message
        """

        return self._msg


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class Task[S]:
    """
    Orchestration for a sequential decision-making problem with state type ``S``
    """

    # Constants
    SENSOR_TIME: str = 'clock'
    """Key associated with the sensor for cycles"""

    SENSOR_TIME_ATTR: str = 'cycles'
    """Attribute produced by the cycle sensor"""

    SENSOR_ELABORATION: str = 'elaboration'
    """Key for the elaboration 'sensor'"""

    ACTUATOR_LOG: str = 'log'
    """Key associated with the log actuator"""

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

    # Phase handling
    _phase_handlers: list[Supplier[bool]]

    #

    def __init__(self, state_initializer: Supplier[S]) -> None:
        """
        :param state_initializer: produces state initially (and on ``reinit``)
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

        # establish phase handling
        # (order dictated by enum)
        _bad_name = "bad"
        _f = stringify(_bad_name)(lambda: False)
        self._phase_handlers = [_f] * len(Phase)
        self._phase_handlers[Phase.ELABORATION] = self._elaborate
        self._phase_handlers[Phase.GOALCHECK] = self._goal_check
        self._phase_handlers[Phase.PROPOSE] = self._propose
        self._phase_handlers[Phase.RANK] = self._rank
        self._phase_handlers[Phase.APPLY] = self._apply
        _changed = (ph for ph in self._phase_handlers if str(ph) != _bad_name)
        assert len(list(_changed)) == len(Phase)

        self.reinit()

    def reinit(self) -> Task[S]:
        """
        Restarts the task

        :return: this task (for chaining)
        """
        self._state = self._state_init()

        self._goal_achieved = False
        self._phase = Phase.ELABORATION
        self._potential_actions = []
        self._ranking = []
        self._chosen = None
        self._step_count = 0
        self._elaboration.clear()

        return self

    def __str__(self) -> str:
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
        :return: current task phase
        """

        return self._phase

    @property
    def done(self) -> bool:
        """
        :return: ``True`` if any goal check has returned ``True``
        """

        return self._goal_achieved

    @property
    def state(self) -> S:
        """
        :return: current task state
        """

        return self._state

    @property
    def num_cycles(self) -> int:
        """
        :return: how many task cycles have occurred since last initialization
        """

        return self._step_count

    @property
    def chosen_action(self) -> Optional[str]:
        """
        :return: ``str()`` of the most recently chosen action
        """
        return None if self._chosen is None else str(self._chosen)

    #

    def add_elaborator(self, e: Elaborator[S]) -> Task[S]:
        """
        Adds a state summarizer to the task

        :param e: elaborator to add
        :return: this task (for chaining)
        """

        self._elaborators.append(e)

        return self

    def elaborator(self, e: Elaborator[S]) -> Elaborator[S]:
        """
        Decorator version of :meth:`Task.add_elaborator`

        :param e: elaborator to add
        :return: added elaborator
        """

        self.add_elaborator(e)
        return e

    def _elaborate(self) -> bool:
        """
        Elaboration phase: allows an opportunity to perform monotonic
                           reasoning over state
        """

        self._elaboration.clear()

        for e in self._elaborators:
            self._elaboration |= e(self._state, self._io)

        return True

    #

    def add_goal_check(self, p: GoalCheck[S]) -> Task[S]:
        """
        Add a task-state predicate to identify a cause of task completion

        :param p: predicate to detect task completion
        :return: this task (for chaining)
        """

        self._goal_checks.append(p)

        return self

    def goal_check(self, p: GoalCheck[S]) -> GoalCheck[S]:
        """
        Decorator version of :meth:`Task.add_goal_check`

        :param p: predicate to add
        :return: added predicate
        """

        self.add_goal_check(p)
        return p

    def _goal_check(self) -> bool:
        """
        GoalCheck phase: task is complete if any goal check returns True
                         (and if so shifts to Propose phase)
        """
        if not self._goal_achieved:
            self._step_count += 1
            self._goal_achieved = any(p(self._state, self._io) for p in self._goal_checks)

        return not self._goal_achieved

    #

    def add_action_factory(self, f: ActionFactory[S]) -> Task[S]:
        """
        Adds a factory to propose potential action(s) given current state

        :param f: factory to add
        :return: this task (for chaining)
        """

        self._action_factories.append(f)

        return self

    def action_factory(self, f: ActionFactory[S]) -> ActionFactory[S]:
        """
        Decorator version of :meth:`Task.add_action_factory`

        :param f: factory to add
        :return: added factory
        """

        self.add_action_factory(f)
        return f

    @staticmethod
    def _make_iterable(
        proposal: Action[S] | Iterable[Action[S]]
    ) -> Iterable[Action[S]]:
        """
        Helps unify processing of either
        one or more actions
        """

        if isinstance(proposal, Iterable):
            return proposal

        return (proposal,)

    def _propose(self) -> bool:
        """
        Propose phase: allow factories to produce candidate actions
                       (and then shift to Rank phase)
        """

        self._potential_actions = list(
            chain.from_iterable(
                Task._make_iterable(f(self._state, self._io))
                for f in self._action_factories
            )
        )

        return True

    #

    def add_action_evaluator(self, ae: ActionEvaluator[S]) -> Task[S]:
        """
        Adds an evaluator of potential actions

        :param ae: evaluator to add
        :return: this task (for chaining)
        """

        self._action_evaluators.append(ae)

        return self

    def action_evaluator(self, ae: ActionEvaluator[S]) -> ActionEvaluator[S]:
        """
        Decorator version of :meth:`Task.add_action_evaluator`

        :param ae: evaluator to add
        :return: added evaluator
        """

        self.add_action_evaluator(ae)
        return ae

    def _rank(self) -> bool:
        """
        Rank phase: allow evaluators to produce action rankings
                    and then select one from amongst the best
                    ranking (and then shift to Apply phase)
        """

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
                    raise TaskExecutionError(TaskErrorMessage.NO_RANK)

                top = list(
                    filter(
                        lambda r: r.rank == self._ranking[0].rank,
                        self._ranking
                    )
                )
                self._chosen = random.sample(top, k=1)[0].a
            else:
                self._chosen = self._potential_actions[0]
        else:
            raise TaskExecutionError(TaskErrorMessage.NO_PROPOSAL)

        return True

    #

    def _apply(self) -> bool:
        """
        Apply phase: executes the selected action (if one exists);
                     state is...
                     * replaced if action produces a result
                     * unchanged by the Task otherwise (assumed
                       to have been modified in-place by the
                       action itself)
        """

        if self._chosen:
            result: Optional[S] = self._chosen(self._state, self._io)
            if result is not None:
                self._state = result
        else:
            raise TaskExecutionError(TaskErrorMessage.NO_CHOICE) # pragma: no cover

        return True

    #

    def run_phase(self) -> Task[S]:
        """
        Executes the current task phase

        :return: this task (for chaining)
        """

        if self._phase_handlers[self._phase]():
            self._phase = self._phase.next

        return self


    def run_cycles(self, n: int = 1) -> Task[S]:
        """
        Executes n cycles of the full task-phases

        :param n: number of task-phases to run
        :return: this task (for chaining)
        """

        for _ in range(n):
            for _ in range(len(Phase)):
                self.run_phase()

        return self

    def run_until_done(self) -> Task[S]:
        """
        Runs until task completion

        :return: this task (for chaining)
        """

        while not self.done:
            self.run_phase()

        return self

    #

    def phases(self) -> Iterator[Task[S]]:
        """
        Facilitates iteration by phase

        :return: (potentially infinite) iterator over task phases
        """

        return TaskIterator(self, True)

    def cycles(self) -> Iterator[Task[S]]:
        """
        Facilitates iteration by cycle

        :return: (potentially infinite) iterator over task cycles
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

    def set_sensor(self, name: str, buffer: Any) -> Task[S]:
        """
        Sets value of ``io.i.name``

        :param name: sensor name
        :param buffer: arbitrary object reference (or ``None`` to remove sensor)
        :return: this task (for chaining)
        """

        Task._set_io_buffer(self._sensors, name, buffer)

        return self

    def set_actuator(self, name: str, buffer: Any) -> Task[S]:
        """
        Sets value of ``io.o.name``

        :param name: actuator name
        :param buffer: arbitrary object reference (or ``None`` to remove actuator)
        :return: this task (for chaining)
        """

        Task._set_io_buffer(self._actuators, name, buffer)

        return self

    @property
    def log(self) -> str:
        """
        :return: any data provided to the :attr:`Task.ACTUATOR_LOG` actuator
        """

        logger: StringIO = cast(StringIO, self._actuators[Task.ACTUATOR_LOG])
        return logger.getvalue()


# pylint: disable=too-few-public-methods
class TimeSensor[S]:
    """
    Sensor (:attr:`Task.SENSOR_TIME`) of the cycle count (via :attr:`Task.SENSOR_TIME_ATTR`)

    :param t: associated task
    """

    def __init__(self, t: Task[S]):
        self._t: Task[S] = t

    @property
    def cycles(self) -> int:
        """
        :return: associated task's cycle count
        """

        return self._t.num_cycles

# pylint: disable=too-few-public-methods
class TaskIterator[S](Iterator[Task[S]]):
    """
    Custom iterator to facilitate easy task iteration via phase or cycle
    """

    def __init__(self, t: Task[S], by_phase: bool = True) -> None:
        """
        :param t: associated task
        :param by_phase: ``True`` if iteration by phase; by cycle otherwise
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
