"""
Base decision process
"""

from __future__ import annotations

import logging
import random
from collections.abc import (
    Iterable,
    Iterator,
)
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from io import StringIO
from itertools import chain
from types import MappingProxyType
from typing import (
    Any,
    Final,
    Self,
    cast,
    no_type_check,
)

from ..util.functypes import (
    BiFunction,
    BiPredicate,
    Supplier,
    TriFunction,
)
from ..util.misc import (
    AttrReferral,
    ImplementsLessThan,
    stringify,
)

# ===

_logger = logging.getLogger(__name__)

# ===

IO_REMOVE: Final[object] = object()
"""Sentinel to used in IO setting to indicate a removal"""


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class IOContainer:
    """
    Convenience bundling of input/output data access
    """

    i: AttrReferral
    """.key access to (i)nput data"""

    o: AttrReferral
    """.key access to (o)utput channels"""

    e: AttrReferral
    """.key access to (e)laborated values"""

    a: AttrReferral
    """.key access to (a)rguments"""

    input: MappingProxyType[str, Any] = field(init=False)
    """Mapping view of i"""

    output: MappingProxyType[str, Any] = field(init=False)
    """Mapping view of o"""

    elab: MappingProxyType[str, Any] = field(init=False)
    """Mapping view of e"""

    args: MappingProxyType[str, Any] = field(init=False)
    """Mapping view of a"""

    def __post_init__(self) -> None:
        object.__setattr__(self, "input", AttrReferral.view(self.i))
        object.__setattr__(self, "output", AttrReferral.view(self.o))
        object.__setattr__(self, "elab", AttrReferral.view(self.e))
        object.__setattr__(self, "args", AttrReferral.view(self.a))


class Phase(IntEnum):
    """
    Representation of decision process phases
    """

    ELABORATION = 0
    """Monotonic summarization of state"""

    TERMINATIONCHECK = 1
    """Detect decision process termination"""

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

type TerminationCheck[S] = BiPredicate[S, IOContainer]
"""Detects decision process termination based upon current state"""

type Action[S] = BiFunction[S, IOContainer, S | None]
"""Changes state via mutation (return ``None``) or replacement (return ``S``)"""

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
        return f"ActionRank(a={self.a !s}, r={self.rank !s})"

    def __lt__(self, other: object) -> bool:
        """
        Smaller rank values come first,
        with a deterministic ordering in
        ties facilitated by action string
        representations

        :param other: ``self`` < ``other``
        :return: ``True`` if comparison holds
        """

        if not isinstance(other, ActionRank):
            return NotImplemented

        return (self.rank < other.rank) or (
            (self.rank == other.rank) and (str(self.a) < str(other.a))
        )


type ActionEvaluator[S] = TriFunction[
    S, IOContainer, Iterable[Action[S]], Iterable[ActionRank[S]]
]
"""Produces rankings of candidate actions"""


class DecisionProcessErrorMessage(StrEnum):
    """
    Known errors with messages
    """

    NO_PROPOSAL = "No potential actions"
    """No candidate actions produced from factories"""

    NO_RANK = "No action rankings"
    """No rankings produced (given multiple candidate actions)"""

    NO_CHOICE = "No chosen action"
    """No action chosen to apply (should not occur)"""


class DecisionProcessExecutionError(Exception):
    """
    A custom exception related to invalid decision process execution

    :param msg: decision process error message
    """

    def __init__(self, msg: DecisionProcessErrorMessage) -> None:
        super().__init__(msg.value)
        self._msg = msg

    @property
    def msg(self) -> DecisionProcessErrorMessage:
        """
        :return: decision process error message
        """

        return self._msg


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class BaseDecisionProcess[S]:
    """
    Orchestration for a sequential decision-making problem with state type ``S``
    """

    # Constants
    INPUT_KEY_TIME: Final[str] = "clock"
    """Key associated with cycle input data"""

    INPUT_ATTR_TIME: Final[str] = "cycles"
    """Attribute produced by the cycle input data"""

    OUTPUT_KEY_LOG: Final[str] = "log"
    """Key associated with the log output channel"""

    # Supplied components...
    _state: S  # arbitrary representation
    _state_init: Supplier[S]  # state start
    _elaborators: list[Elaborator[S]]  # elaborates state each cycle
    _termination_checks: list[
        TerminationCheck[S]
    ]  # determines if the decision process terminated
    _action_factories: list[
        ActionFactory[S]
    ]  # identifying potential next decision process steps
    _action_evaluators: list[ActionEvaluator[S]]  # ranking for supplied actions

    # Internal decision process state...
    _terminated: bool  # is the current decision process terminated?
    _phase: Phase  # current phase of decision process
    _potential_actions: list[Action[S]]  # last computed set of potential actions
    _ranking: list[ActionRank[S]]  # last computed set of action ranking
    _chosen: Action[S] | None  # last selected action
    _step_count: int  # number of decision cycles since last initialization

    # Input/Output/Elaboration/Args
    _inputs: dict[str, Any]
    _outputs: dict[str, Any]
    _elabs: dict[str, Any]
    _args: dict[str, Any]
    _io: IOContainer

    # Phase handling
    _phase_handlers: list[Supplier[bool]]

    # ===

    @no_type_check
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["_io"]
        return state

    @no_type_check
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._setup_io()

    def _setup_io(self) -> None:
        self._io = IOContainer(
            AttrReferral(self._inputs),
            AttrReferral(self._outputs),
            AttrReferral(self._elabs),
            AttrReferral(self._args),
        )

    def __init__(self, state_initializer: Supplier[S]) -> None:
        """
        :param state_initializer: produces state initially (and on :meth:`reinit`)
        """

        _logger.info("%s: initialization started", type(self).__name__)
        _logger.debug("state_init=%s", state_initializer)

        self._state_init = state_initializer
        self._elaborators = []
        self._termination_checks = []
        self._action_factories = []
        self._action_evaluators = []

        self._inputs = {
            BaseDecisionProcess.INPUT_KEY_TIME: _InnerClock(self),
        }
        self._outputs = {BaseDecisionProcess.OUTPUT_KEY_LOG: _InnerLog()}
        self._elabs = {}
        self._args = {}
        self._setup_io()

        # establish phase handling
        # (order dictated by enum)
        _bad_name = "bad"
        _f = stringify(_bad_name)(lambda: False)
        self._phase_handlers = [_f] * len(Phase)
        self._phase_handlers[Phase.ELABORATION] = self._elaborate
        self._phase_handlers[Phase.TERMINATIONCHECK] = self._termination_check
        self._phase_handlers[Phase.PROPOSE] = self._propose
        self._phase_handlers[Phase.RANK] = self._rank
        self._phase_handlers[Phase.APPLY] = self._apply
        _changed = (ph for ph in self._phase_handlers if str(ph) != _bad_name)
        assert len(list(_changed)) == len(Phase)

        self.reinit()

        _logger.debug("state=%s", self.state)
        _logger.info("%s: initialization complete", type(self).__name__)

    def reinit(self) -> Self:
        """
        Restarts the decision process

        :return: this decision process (for chaining)
        """

        _logger.info("%s: reinit started", type(self).__name__)

        self._state = self._state_init()

        self._terminated = False
        self._phase = Phase.ELABORATION
        self._potential_actions = []
        self._ranking = []
        self._chosen = None
        self._step_count = 0
        self._elabs.clear()

        _logger.info("%s: reinit complete", type(self).__name__)

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
                "Termination Checks": ", ".join(
                    str(p) for p in self._termination_checks
                ),
                "Elaborators": ", ".join(str(e) for e in self._elaborators),
                "Input Sources": ", ".join(s for s in self._inputs),
                "Output Channels": ", ".join(a for a in self._outputs),
                "Elaborated Data": ", ".join(
                    f"{k}:{v!s}" for k, v in self._elabs.items()
                ),
                "Argument Values": ", ".join(
                    f"{k}:{v!s}" for k, v in self._args.items()
                ),
            }.items()
        )

    @property
    def phase(self) -> Phase:
        """
        :return: current decision process phase
        """

        return self._phase

    @property
    def done(self) -> bool:
        """
        :return: ``True`` if any termination check has returned ``True``
        """

        return self._terminated

    @property
    def state(self) -> S:
        """
        :return: current decision process state
        """

        return self._state

    @property
    def io(self) -> IOContainer:
        """
        :return: current decision process io (for debugging)
        """

        return self._io

    @property
    def num_cycles(self) -> int:
        """
        :return: how many decision process cycles have occurred since last initialization
        """

        return self._step_count

    @property
    def chosen_action(self) -> str | None:
        """
        :return: ``str()`` of the most recently chosen action
        """
        return None if self._chosen is None else str(self._chosen)

    # ===

    def add_elaborator(self, e: Elaborator[S]) -> Self:
        """
        Adds a state summarizer to the decision process

        :param e: elaborator to add
        :return: this decision process (for chaining)
        """

        self._elaborators.append(e)

        _logger.info("%s: elaborator added", type(self).__name__)
        _logger.debug(e)

        return self

    def elaborator(self, e: Elaborator[S]) -> Elaborator[S]:
        """
        Decorator version of :meth:`add_elaborator`

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

        _logger.info("%s: elaboration phase started", type(self).__name__)
        _logger.debug(
            "state=%s, i=%s, o=%s",
            self._state,
            {k: str(v) for k, v in self._io.input.items()},
            {k: str(v) for k, v in self._io.output.items()},
        )

        self._elabs.clear()

        _logger.debug("%s: prior elaboration values cleared", type(self).__name__)

        for e in self._elaborators:
            _logger.debug("%s: running elaborator (%s)", type(self).__name__, e)
            result = e(self._state, self._io)
            _logger.debug(result)

            self._elabs |= result

        _logger.debug("%s: union=%s", type(self).__name__, self._elabs)
        _logger.info("%s: elaboration phase complete", type(self).__name__)

        return True

    # ===

    def add_termination_check(self, p: TerminationCheck[S]) -> Self:
        """
        Add a state predicate to identify a cause of decision process termination

        :param p: predicate to detect termination
        :return: this decision process (for chaining)
        """

        self._termination_checks.append(p)

        _logger.info("%s: termination check added", type(self).__name__)
        _logger.debug(p)

        return self

    def termination_check(self, p: TerminationCheck[S]) -> TerminationCheck[S]:
        """
        Decorator version of :meth:`add_termination_check`

        :param p: predicate to add
        :return: added predicate
        """

        self.add_termination_check(p)
        return p

    def _termination_check(self) -> bool:
        """
        TerminationCheck phase: decision process is complete if any termination check returns True
                                (and if so shifts to Propose phase)
        """

        _logger.info("%s: termination_check phase started", type(self).__name__)
        _logger.debug("already terminated: %s", self._terminated)

        if not self._terminated:
            self._step_count += 1
            _logger.debug("cycles: %s -> %s", self._step_count - 1, self._step_count)

            self._terminated = any(
                p(self._state, self._io) for p in self._termination_checks
            )
            _logger.debug("now terminated: %s", self._terminated)

        _logger.info("%s: termination_check phase completed", type(self).__name__)

        return not self._terminated

    # ===

    def add_action_factory(self, f: ActionFactory[S]) -> Self:
        """
        Adds a factory to propose potential action(s) given current state

        :param f: factory to add
        :return: this decision process (for chaining)
        """

        self._action_factories.append(f)

        _logger.info("%s: action factory added", type(self).__name__)
        _logger.debug(f)

        return self

    def action_factory(self, f: ActionFactory[S]) -> ActionFactory[S]:
        """
        Decorator version of :meth:`add_action_factory`

        :param f: factory to add
        :return: added factory
        """

        self.add_action_factory(f)
        return f

    @staticmethod
    def _make_iterable(
        proposal: Action[S] | Iterable[Action[S]],
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

        _logger.info("%s: proposal phase started", type(self).__name__)

        self._potential_actions = list(
            chain.from_iterable(
                BaseDecisionProcess._make_iterable(f(self._state, self._io))
                for f in self._action_factories
            )
        )

        _logger.debug(tuple(str(pa) for pa in self._potential_actions))

        _logger.info("%s: proposal phase completed", type(self).__name__)

        return True

    # ===

    def add_action_evaluator(self, ae: ActionEvaluator[S]) -> Self:
        """
        Adds an evaluator of potential actions

        :param ae: evaluator to add
        :return: this decision process (for chaining)
        """

        self._action_evaluators.append(ae)

        _logger.info("%s: action evaluator added", type(self).__name__)
        _logger.debug(ae)

        return self

    def action_evaluator(self, ae: ActionEvaluator[S]) -> ActionEvaluator[S]:
        """
        Decorator version of :meth:`add_action_evaluator`

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

        _logger.info("%s: rank phase started", type(self).__name__)

        self._chosen = None

        if self._potential_actions:
            self._ranking = []

            if len(self._potential_actions) > 1:
                _logger.debug(
                    "%s: multiple actions, so querying evaluator(s)",
                    type(self).__name__,
                )

                self._ranking = sorted(
                    chain.from_iterable(
                        ae(self._state, self._io, self._potential_actions)
                        for ae in self._action_evaluators
                    )
                )

                _logger.debug(tuple(str(r) for r in self._ranking))

                if len(self._ranking) == 0:
                    e = DecisionProcessExecutionError(
                        DecisionProcessErrorMessage.NO_RANK
                    )

                    _logger.error(e)
                    raise e

                _logger.debug(
                    "%s: at least one ranking produced, so randomly choosing from top",
                    type(self).__name__,
                )

                top = list(
                    filter(lambda r: r.rank == self._ranking[0].rank, self._ranking)
                )
                self._chosen = random.sample(top, k=1)[0].a

                _logger.debug(self._chosen)
            else:
                self._chosen = self._potential_actions[0]

                _logger.debug(
                    "%s: only one potential action, and so selected",
                    type(self).__name__,
                )
                _logger.debug(self._chosen)
        else:
            e = DecisionProcessExecutionError(DecisionProcessErrorMessage.NO_PROPOSAL)

            _logger.error(e)
            raise e

        _logger.info("%s: rank phase completed", type(self).__name__)

        return True

    # ===

    def _apply(self) -> bool:
        """
        Apply phase: executes the selected action (if one exists);
                     state is...
                     * replaced if action produces a result
                     * unchanged  otherwise (assumed to
                       have been modified in-place by the
                       action itself)
        """

        _logger.info("%s: apply phase started", type(self).__name__)

        if self._chosen:
            _logger.debug("%s: running chosen action", type(self).__name__)

            result: S | None = self._chosen(self._state, self._io)

            _logger.debug(result)

            if result is not None:
                _logger.debug(
                    "%s: non-None result, so replacing state", type(self).__name__
                )
                self._state = result
        else:  # pragma: no cover
            e = DecisionProcessExecutionError(DecisionProcessErrorMessage.NO_CHOICE)

            _logger.error(e)
            raise e

        _logger.info("%s: apply phase completed", type(self).__name__)

        return True

    # ===

    def run_phase(self) -> Self:
        """
        Executes the current decision process phase

        :return: this decision process (for chaining)
        """

        if self._phase_handlers[self._phase]():
            self._phase = self._phase.next

        return self

    def run_cycles(self, n: int = 1) -> Self:
        """
        Executes (up to) n cycles of the full phases

        :param n: number of phases to run
        :return: this decision process (for chaining)
        """

        for _ in range(n):
            for _ in range(len(Phase)):
                self.run_phase()

        return self

    def run_until_done(self) -> Self:
        """
        Runs until decision process completion

        :return: this decision process (for chaining)
        """

        while not self.done:
            self.run_phase()

        return self

    # ===

    def phases(self) -> Iterator[Self]:
        """
        Facilitates iteration by phase

        :return: (potentially infinite) iterator over phases
        """

        return DecisionProcessIterator(self, True)

    def cycles(self) -> Iterator[Self]:
        """
        Facilitates iteration by cycle

        :return: (potentially infinite) iterator over cycles
        """

        return DecisionProcessIterator(self, False)

    # ===

    @staticmethod
    def _set_io(d: dict[str, Any], key: str, data: Any) -> None:
        """Abstraction for io setting"""

        if data is IO_REMOVE:
            d.pop(key, None)
        else:
            d[key] = data

    def _set_io_key_value(
        self, d: dict[str, Any], key: str, data: Any, key_name: str
    ) -> Self:
        """Abstraction for logged io setting"""

        BaseDecisionProcess._set_io(d, key, data)

        type_name = type(self).__name__
        if data is IO_REMOVE:
            _logger.info("%s: %s (%s) removed", type_name, key_name, key)
        else:
            _logger.info("%s: %s (%s) set", type_name, key_name, key)
            _logger.debug(data)

        return self

    def set_input_data(self, input_key: str, data: Any) -> Self:
        """
        Sets value of ``io.i.input_key``

        :param name: input data key
        :param buffer: arbitrary object reference (or ``IO_REMOVE`` to remove)
        :return: this decision process (for chaining)
        """

        return self._set_io_key_value(self._inputs, input_key, data, "input data")

    def set_output_channel(self, output_key: str, data: Any) -> Self:
        """
        Sets value of ``io.o.output_key``

        :param name: output channel key
        :param buffer: arbitrary object reference (or ``IO_REMOVE`` to remove)
        :return: this decision process (for chaining)
        """

        return self._set_io_key_value(self._outputs, output_key, data, "output channel")

    def set_arg_value(self, arg_key: str, data: Any) -> Self:
        """
        Sets value of ``io.a.arg_key``

        :param name: argument key
        :param buffer: arbitrary object reference (or ``IO_REMOVE`` to remove)
        :return: this decision process (for chaining)
        """

        return self._set_io_key_value(self._args, arg_key, data, "argument value")

    # ===

    @property
    def log(self) -> str:
        """
        :return: any data provided to the :attr:`OUTPUT_KEY_LOG` channel
        """

        logger = cast(_InnerLog, self._outputs[BaseDecisionProcess.OUTPUT_KEY_LOG])
        return str(logger)

    def clear_log(self) -> Self:
        """
        Clears any data provided to the :attr:`OUTPUT_KEY_LOG` channel

        :return: this decision process (for chaining)
        """

        logger = cast(_InnerLog, self._outputs[BaseDecisionProcess.OUTPUT_KEY_LOG])
        logger.clear()

        return self


# pylint: disable=too-few-public-methods
class _InnerClock[S]:
    """action access to dp cycles"""

    def __init__(self, dp: BaseDecisionProcess[S]):
        setattr(
            type(self),
            BaseDecisionProcess.INPUT_ATTR_TIME,
            property(lambda _: dp.num_cycles),
        )

    def __str__(self) -> str:
        return (
            f"{_InnerClock.__name__}"
            f"({BaseDecisionProcess.INPUT_ATTR_TIME}="
            f"{getattr(self, BaseDecisionProcess.INPUT_ATTR_TIME)})"
        )


class _InnerLog(StringIO):
    """string i/o + convenience methods"""

    def __str__(self) -> str:
        return self.getvalue()

    def clear(self) -> None:
        """
        Clears the buffer
        """

        self.truncate(0)
        self.seek(0)


# pylint: disable=too-few-public-methods
class DecisionProcessIterator[S, DP: BaseDecisionProcess[S]](  # type: ignore[name-defined]
    Iterator[DP]
):
    """
    Custom iterator to facilitate easy decision process iteration via phase or cycle
    """

    def __init__(self, dp: DP, by_phase: bool = True) -> None:
        """
        :param dp: associated decision process
        :param by_phase: ``True`` if iteration by phase; by cycle otherwise
        """

        self._dp: DP = dp
        self._by_phase: bool = by_phase

    def __next__(self) -> DP:
        """
        Provides the next phase/cycle
        if the decision process is not complete
        """

        if self._dp.done:
            raise StopIteration

        if self._by_phase:
            self._dp.run_phase()
        else:
            self._dp.run_cycles()

        return self._dp
