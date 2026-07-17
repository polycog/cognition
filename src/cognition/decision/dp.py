"""
Practical library additions
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Self, TYPE_CHECKING, cast, runtime_checkable

from abc import ABC, abstractmethod

from collections.abc import (
    Generator,
    Iterable,
    Mapping,
)

from types import MappingProxyType

from enum import IntEnum

from contextlib import contextmanager

from functools import cmp_to_key

from ..util.functypes import (
    BiFunction,
    Function,
    Predicate,
    Supplier,
    TriFunction,
)

from ..util.misc import (
    AttrReferral,
    ImplementsLessThan,
    optionally_name,
    stringify,
)

from .core import (
    Action,
    ActionEvaluator,
    ActionFactory,
    ActionRank,
    BaseDecisionProcess,
    Elaborator,
    IOContainer,
    Phase,
)

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons

#

OPERATOR_SELF_PARAM: str = "_op"
"""Default :class:`NamedAction` parameter key to access source operator"""

ARGS_ATTR: str = "args"
"""io.i.name for run arguments"""


class Rank(IntEnum):
    """
    Example 3-level rankings of actions
    """

    HIGH = 1
    """High importance"""

    MEDIUM = 2
    """Medium importance"""

    LOW = 3
    """Low importance"""


#


def _add_args[S](
    t: BaseDecisionProcess[S], namespace: str, **info: Any
) -> Generator[BaseDecisionProcess[S], None, None]:
    """
    Provides `io.i.namespace` temporarily

    :param t: task for which to provide arguments
    :param namespace: sensor name
    :param info: io.i.namespace.key=value
    """

    try:
        t.set_sensor(namespace, AttrReferral(info))
        yield t
    finally:
        t.set_sensor(namespace, None)


@contextmanager
def args_added[S](
    t: BaseDecisionProcess[S], namespace: str = ARGS_ATTR, **info: Any
) -> Generator[BaseDecisionProcess[S], None, None]:
    """
    Provides `io.i.namespace` temporarily

    :param t: task for which to provide arguments
    :param namespace: sensor name
    :param info: io.i.namespace.key=value
    """

    yield from _add_args(t, namespace, **info)


def create_elaborator[S](
    name: Optional[str] = None, **kwargs: BiFunction[S, IOContainer, Any]
) -> Elaborator[S]:
    """
    Elaborator generator given association between keywords and value-producing functions

    :param name: optional name
    :param kwargs: ``key=value(state, io)``
    :return: resulting elaborator
    """

    def _f(s: S, io: IOContainer) -> dict[str, Any]:
        return {k: v(s, io) for k, v in kwargs.items()}

    return optionally_name(_f, name)


def _qualified_name(name: str, **kwargs: Any) -> str:
    """
    Naming convention for a combo of name + optional params
    (ignoring those whose name starts with an underscore)
    """

    true_args = {k: v for k, v in kwargs.items() if k[:1] != "_"}

    if true_args:
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in true_args.items())

        return f"{name}[{params_str}]"

    return name


# pylint: disable=too-few-public-methods
@runtime_checkable
class NamedAction(Protocol):
    """
    An action that has name/params annotations
    """

    name: str
    """Action name"""

    params: MappingProxyType[str, Any]
    """Action parameters"""


def create_named_action[S](name: str, f: Action[S], **kwargs: Any) -> Action[S]:
    """
    Annotates an action via ``str()`` and attributes

    :param name: name to add
    :param f: original action
    :param kwargs: arbitrary keyword=value pairs
    :return: :class:`NamedAction` + :func:`.utility.stringify`
    """

    new_f = stringify(_qualified_name(name, **kwargs))(f)

    # pylint: disable=attribute-defined-outside-init
    new_named = cast(NamedAction, new_f)
    new_named.name = name
    new_named.params = MappingProxyType(kwargs.copy())

    return new_f


class BaseOperator[S](Protocol):
    """
    Pattern to support a predicate gating a single action
    """

    def can_perform(self, state: S, io: IOContainer) -> bool:
        """
        Does this hold in the current state?

        :param state: current state
        :param io: access to sensors/actuators
        :return: ``True`` if the action applies in the current state
        """

    def perform(self, state: S, io: IOContainer) -> Optional[S]:
        """
        Action to perform if selected (see :class:`.core.Action`)
        """

    @property
    def name(self) -> str:
        """
        :return: how to refer to the resulting action [and factory]
        """

    @property
    def params(self) -> Mapping[str, Any]:
        """
        :return: optional augmentations in the name
        """


class Operator[S](ABC, BaseOperator[S]):
    """
    Operator interface
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """
        :param name: name for the protocol
        :param kwargs: params for the protocol
        """

        self._name = name
        self._params = MappingProxyType(kwargs.copy())

    @abstractmethod
    def can_perform(self, state: S, io: IOContainer) -> bool:
        """See :meth:`BaseOperator.can_perform`"""

    @abstractmethod
    def perform(self, state: S, io: IOContainer) -> Optional[S]:
        """See :meth:`BaseOperator.perform`"""

    @property
    def name(self) -> str:
        """
        :return: name supplied upon construction
        """

        return self._name

    @property
    def params(self) -> MappingProxyType[str, Any]:
        """
        :return: params supplied upon construction
        """

        return self._params


def add_operator[S](
    task: BaseDecisionProcess[S],
    op: BaseOperator[S],
    self_param: Optional[str] = OPERATOR_SELF_PARAM,
) -> tuple[ActionFactory[S], Action[S]]:
    """
    Instantiates the operator within a task

    :param task: task to be added to
    :param op: operator with factory/action info
    :param self_param: if not ``None``, action param referring to the op
    :return: the produced action factory and action
    """

    factory_pred = op.can_perform

    act_params = dict(op.params)
    if self_param is not None:
        act_params[self_param] = op

    op_action = create_named_action(op.name, op.perform, **act_params)

    @task.action_factory
    @stringify(op.name)
    def action_factory(s: S, io: IOContainer) -> Iterable[Action[S]]:
        """propose performing if can perform"""

        if factory_pred(s, io):
            return [op_action]

        return []

    return action_factory, op_action


def uniform_evaluator[S](
    r: ImplementsLessThan,
    p: Predicate[Action[S]] = lambda _: True,
    name: Optional[str] = None,
) -> ActionEvaluator[S]:
    """
    Applies a supplied rank to all potential actions that satisfy a predicate

    :param r: rank to uniformly apply
    :param p: optional predicate to gate potential actions
    :param name: optional name of the evaluator
    :return: resulting evaluator
    """

    def evaluation_func(
        _state: S, _io: IOContainer, potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:
        return (ActionRank(a, r) for a in potential_actions if p(a))

    return optionally_name(evaluation_func, name)


def sorting_evaluator[S](
    sorting_key: TriFunction[Action[S], S, IOContainer, "SupportsAllComparisons"],
    rank_start: int = 1,
    name: Optional[str] = None,
) -> ActionEvaluator[S]:
    """
    Associates rankings based upon relative sorting order over actions

    :param sorting_key: key function for ``sort()`` to order actions
    :param rank_start: starting value for produced ranks
    :param name: optional name for the evaluator
    :return: resulting evaluator
    """

    def evaluation_func(
        state: S, io: IOContainer, potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:

        ordered = sorted(potential_actions, key=lambda a: sorting_key(a, state, io))

        current_rank: int = rank_start
        ranks = [current_rank] * len(ordered)

        for i in range(1, len(ordered)):
            key_curr = sorting_key(ordered[i], state, io)
            key_prev = sorting_key(ordered[i - 1], state, io)

            if key_curr != key_prev:
                current_rank += 1

            ranks[i] = current_rank

        return (ActionRank(e, r) for e, r in zip(ordered, ranks))

    return optionally_name(evaluation_func, name)


def operator_sorting_key[S](
    op_param: str = OPERATOR_SELF_PARAM,
) -> TriFunction[Action[S], S, IOContainer, "SupportsAllComparisons"]:
    """
    Produces an action sorting key for actions derived from named operators

    :param op_param: action param key for operator self-reference
    :return: key function
    """

    def cmp(a: Action[S], b: Action[S]) -> int:
        op_a = cast(NamedAction, a).params[op_param]
        op_b = cast(NamedAction, b).params[op_param]

        if op_a == op_b:
            return 0

        if op_a < op_b:
            return -1

        return 1

    return lambda a, _s, _io: cmp_to_key(cmp)(a)


TERMINAL_ACTION_ATTR: str = "terminal"
"""Attribute name to trigger termination for a selected action"""


class DecisionProcess[S](BaseDecisionProcess[S]):
    """
    Support for optional decision process add-ons
    """

    def __init__(
        self,
        state_initializer: Supplier[S],
        enable_terminal_check: bool = False,
    ) -> None:
        """
        :param state_initializer: produces state initially (and on ``reinit``)
        :param enable_terminal_check: if True, a selected :class:`NamedAction` with a
                                      :const:`TERMINAL_ACTION_ATTR` parameter
                                      triggers termination during check
        """

        super().__init__(state_initializer)

        if enable_terminal_check:
            self._phase_handlers[Phase.TERMINATIONCHECK] = self._terminal_check

    @contextmanager
    def args_added(
        self, namespace: str = ARGS_ATTR, **info: Any
    ) -> Generator[BaseDecisionProcess[S], None, None]:
        """
        Pass-thru to :func:`args_added`

        :param info: io.i.namespace.key=value
        """

        yield from _add_args(self, namespace, **info)

    def add_operator(
        self, op: BaseOperator[S], self_param: Optional[str] = OPERATOR_SELF_PARAM
    ) -> tuple[ActionFactory[S], Action[S], Self]:
        """
        Pass-thru to :func:`add_operator`.

        :param op: operator with factory/action info
        :param self_param: if not ``None``, action param referring to the op
        :return: the produced action factory and action, and this task (for chaining)
        """

        af, a = add_operator(self, op, self_param)
        return af, a, self

    def add_operator_c(
        self, op: BaseOperator[S], self_param: Optional[str] = OPERATOR_SELF_PARAM
    ) -> Self:
        """
        Pass-thru to :meth:`DecisionProcess.add_operator`.

        :param op: operator with factory/action info
        :param self_param: if not ``None``, action param referring to the op
        :return: this task (for chaining)
        """

        self.add_operator(op, self_param)
        return self

    def operator(
        self,
        op_name: str,
        self_param: Optional[str] = OPERATOR_SELF_PARAM,
        **kwargs: Any,
    ) -> Function[type[Operator[S]], type[Operator[S]]]:
        """
        Decorator version of :meth:`DecisionProcess.add_operator`
        that assumes instantiation takes a positional name
        and arbitrary keywords

        :param op_name: name to give to the added instance
        :param self_param: if not ``None``, action param referring to the op
        :param kwargs: operator params
        :return: parameterized named-object decorator
        """

        def cls_dec(cls: type[Operator[S]]) -> type[Operator[S]]:
            """
            Parameterized named-object decorator that adds an
            operator instance to this task.

            :param cls: named operator to instantiate
            :return: added class
            """

            self.add_operator(cls(op_name, **kwargs), self_param)

            return cls

        return cls_dec

    def _terminal_check(self) -> bool:
        """
        Custom termination check, adding possibility of terminal actions
        """

        if not self._terminated:
            if isinstance(self._chosen, NamedAction):
                self._terminated = TERMINAL_ACTION_ATTR in self._chosen.params

        return super()._termination_check()

    def __call__(
        self,
        max_cycles: Optional[int] = None,
        suppress_errors: bool = True,
        args_namespace: str = ARGS_ATTR,
        **args: Any,
    ) -> Optional[S]:
        """
        Execute the task, function-style

        :param max_cycles: maximum steps to execute
        :param suppress_errors: if `True`, does not raise any errors from execution
        :param args_namespace: argument sensor name
        :param args: arguments to supply
        :return: the final state if the task completed without
                 any exceptions; None otherwise
        """

        with self.args_added(namespace=args_namespace, **args):
            try:
                if max_cycles is None:
                    self.run_until_done()
                else:
                    self.run_cycles(max_cycles)
            except Exception as err:  # pylint: disable=broad-exception-caught
                if not suppress_errors:
                    raise RuntimeError("Failed to run") from err

                return None

        if not self.done:
            return None

        return self.state
