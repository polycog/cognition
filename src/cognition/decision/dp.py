"""
Decision process (with batteries included)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import (
    Generator,
    Iterable,
)
from contextlib import contextmanager
from enum import IntEnum
from functools import cmp_to_key
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, Self, cast, runtime_checkable

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

# ===

OPERATOR_SELF_PARAM: str = "_op"
"""Default :class:`NamedObject` parameter key to access source operator"""

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


# ===


def _add_args[S](
    dp: BaseDecisionProcess[S], namespace: str, **info: Any
) -> Generator[BaseDecisionProcess[S]]:
    """
    Provides `io.i.namespace` temporarily

    :param dp: decision process for which to provide arguments
    :param namespace: input source name
    :param info: io.i.namespace.key=value
    """

    try:
        dp.set_input_data(namespace, AttrReferral(info))
        yield dp
    finally:
        dp.set_input_data(namespace, None)


@contextmanager
def args_added[S](
    dp: BaseDecisionProcess[S], namespace: str = ARGS_ATTR, **info: Any
) -> Generator[BaseDecisionProcess[S]]:
    """
    Provides `io.i.namespace` temporarily

    :param dp: decision process for which to provide arguments
    :param namespace: input source name
    :param info: io.i.namespace.key=value
    """

    yield from _add_args(dp, namespace, **info)


def create_elaborator[S](
    name: str | None = None, **kwargs: BiFunction[S, IOContainer, Any]
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


# pylint: disable=too-few-public-methods
@runtime_checkable
class NamedObject(Protocol):
    """
    An object that has name/params annotations
    """

    @property
    def name(self) -> str:
        """
        :return: object name
        """

    @property
    def params(self) -> MappingProxyType[str, Any]:
        """
        :return: optional augmentations in the name
        """


def _format_name_params(name: str, **kwargs: Any) -> str:
    """
    Naming convention for a combo of name + optional params
    (ignoring those whose name starts with an underscore)

    :param name: item name
    :param kwargs: optional params
    :return: "name" or "name[arg1=val1, arg2=val2, ...]"
    """

    true_args = {k: v for k, v in kwargs.items() if k[:1] != "_"}

    if true_args:
        params_str = ", ".join(f"{k}={v !r}" for k, v in true_args.items())

        return f"{name}[{params_str}]"

    return name


def create_named_action[S](name: str, f: Action[S], **kwargs: Any) -> Action[S]:
    """
    Annotates an action via ``str()`` and attributes

    :param name: name to add
    :param f: original action
    :param kwargs: arbitrary keyword=value pairs
    :return: :class:`NamedObject` + :func:`.utility.stringify`
    """

    new_f = stringify(_format_name_params(name, **kwargs))(f)

    new_f.name = name  # type: ignore[attr-defined]
    new_f.params = MappingProxyType(kwargs)  # type: ignore[attr-defined]

    return new_f


class _BaseOperator[S](ABC, NamedObject):
    """
    Common functionality across operators
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """
        :param name: name for the resulting action [and factory]
        :param kwargs: optional params for the resulting action
        """

        self._name = name
        self._params = MappingProxyType(kwargs.copy())

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

    @abstractmethod
    def perform(self, state: S, io: IOContainer) -> S | None:
        """
        Action to perform if selected (see :class:`.core.Action`)
        """


class OperatorGenerator[S, X](_BaseOperator[S]):
    """
    A pattern for generating state-specific action(s)
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(type(self).get_name(), **kwargs)

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """
        :return: name for all generated instances
        """

    @classmethod
    @abstractmethod
    def generate(cls, state: S, io: IOContainer, extra: X) -> Iterable[Self]:
        """
        Produces action(s) that hold in the current state

        :param state: current state
        :param io: access to input/output
        :param extra: generator-specific data
        :return: applicable action(s)
        """


class Operator[S](_BaseOperator[S]):
    """
    A predicate gating a single action
    """

    @abstractmethod
    def can_perform(self, state: S, io: IOContainer) -> bool:
        """
        Does the action hold in the current state?

        :param state: current state
        :param io: access to input/output
        :return: ``True`` if the action applies in the current state
        """


def _maybe_augment_params[S](
    op: _BaseOperator[S], self_param: str | None
) -> dict[str, Any]:
    act_params = dict(op.params)
    if self_param is not None:
        act_params[self_param] = op

    return act_params


def add_generator[S, X](
    dp: BaseDecisionProcess[S],
    gen_type: type[OperatorGenerator[S, X]],
    extra: X,
    self_param: str | None = OPERATOR_SELF_PARAM,
) -> ActionFactory[S]:
    """
    Instantiates the generator within a decision process

    :param dp: decision process to be added to
    :param gen_type: source of operators
    :param extra: generator-specific data
    :param cmp_param: if not ``None``, action param -> the produced ops (for purposes of comparison)
    :return: the produced action factory
    """

    op_generator = gen_type.generate

    @dp.action_factory
    @stringify(gen_type.get_name())
    def action_factory(s: S, io: IOContainer) -> Iterable[Action[S]]:
        """allow the generator to propose"""

        yield from (
            create_named_action(
                op.name, op.perform, **_maybe_augment_params(op, self_param)
            )
            for op in op_generator(s, io, extra)
        )

    return action_factory


def add_operator[S](
    dp: BaseDecisionProcess[S],
    op: Operator[S],
    self_param: str | None = OPERATOR_SELF_PARAM,
) -> tuple[ActionFactory[S], Action[S]]:
    """
    Instantiates the operator within a decision process

    :param dp: decision process to be added to
    :param op: operator with factory/action info
    :param self_param: if not ``None``, action param referring to the op
    :return: the produced action factory and action
    """

    factory_pred = op.can_perform
    op_action = create_named_action(
        op.name, op.perform, **_maybe_augment_params(op, self_param)
    )

    @dp.action_factory
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
    name: str | None = None,
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
    sorting_key: TriFunction[Action[S], S, IOContainer, SupportsAllComparisons],
    p: Predicate[Action[S]] = lambda _: True,
    rank_start: int = 1,
    name: str | None = None,
) -> ActionEvaluator[S]:
    """
    Associates rankings based upon relative sorting order over actions

    :param sorting_key: key function for ``sort()`` to order actions
    :param p: optional predicate to gate potential actions
    :param rank_start: starting value for produced ranks
    :param name: optional name for the evaluator
    :return: resulting evaluator
    """

    def evaluation_func(
        state: S, io: IOContainer, potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:

        ordered = sorted(
            (pa for pa in potential_actions if p(pa)),
            key=lambda a: sorting_key(a, state, io),
        )

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
) -> TriFunction[Action[S], S, IOContainer, SupportsAllComparisons]:
    """
    Produces an action sorting key for actions derived from operators

    :param op_param: action param key for operator self-reference
    :return: key function
    """

    def cmp(a: Action[S], b: Action[S]) -> int:
        op_a = cast(NamedObject, a).params[op_param]
        op_b = cast(NamedObject, b).params[op_param]

        if op_a == op_b:
            return 0

        if op_a < op_b:
            return -1

        return 1

    return lambda a, _s, _io: cmp_to_key(cmp)(a)


@runtime_checkable
class Elaborable[S](Protocol):
    """
    Defines a state that supplies an
    elaborator, to be added to a decision
    process upon initialization
    """

    @property
    @abstractmethod
    def elaborator(self) -> Elaborator[S]:
        """
        Provide the state-specific elaborator

        :return: state-specific elaborator
        """


TERMINAL_ACTION_ATTR: str = "terminal"
"""Attribute name to trigger termination for a selected action"""


class DecisionProcess[S](BaseDecisionProcess[S]):
    """
    Decision process implementation with batteries included
    """

    def __init__(
        self,
        state_initializer: Supplier[S],
        enable_terminal_check: bool = False,
    ) -> None:
        """
        :param state_initializer: produces state initially (and on ``reinit``)
        :param enable_terminal_check: if True, a selected named action
                                      (:func:`create_named_action`) with a
                                      :const:`TERMINAL_ACTION_ATTR` parameter
                                      triggers termination during check
        """

        super().__init__(state_initializer)

        if isinstance(self._state, Elaborable):
            self.add_elaborator(self._state.elaborator)

        if enable_terminal_check:
            self._phase_handlers[Phase.TERMINATIONCHECK] = self._terminal_check

    @contextmanager
    def args_added(
        self, namespace: str = ARGS_ATTR, **info: Any
    ) -> Generator[BaseDecisionProcess[S]]:
        """
        Pass-thru to :func:`args_added`

        :param info: io.i.namespace.key=value
        """

        yield from _add_args(self, namespace, **info)

    def add_generator[X](
        self,
        gen_type: type[OperatorGenerator[S, X]],
        extra: X,
        self_param: str | None = OPERATOR_SELF_PARAM,
    ) -> tuple[ActionFactory[S], Self]:
        """
        Pass-thru to :func:`add_generator`.

        :param gen_type: source of operators
        :param self_param: if not ``None``, action param referring to the op
        :param extra: generator-specific data
        :return: the produced action factory and this decision process (for chaining)
        """

        return add_generator(self, gen_type, extra, self_param), self

    def add_generator_c[X](
        self,
        gen_type: type[OperatorGenerator[S, X]],
        extra: X,
        self_param: str | None = OPERATOR_SELF_PARAM,
    ) -> Self:
        """
        Pass-thru to :meth:`DecisionProcess.add_generator`.

        :param gen_type: source of operators
        :param extra: generator-specific data
        :param self_param: if not ``None``, action param referring to the op
        :return: this decision process (for chaining)
        """

        return self.add_generator(gen_type, extra, self_param)[1]

    def generator[X](
        self, extra: X, self_param: str | None = OPERATOR_SELF_PARAM
    ) -> Function[type[OperatorGenerator[S, X]], type[OperatorGenerator[S, X]]]:
        """
        Decorator version of :meth:`DecisionProcess.add_generator`

        :param extra: generator-specific data
        :param self_param: if not ``None``, action param referring to the op
        :return: parameterized decorator
        """

        def cls_dec(
            cls: type[OperatorGenerator[S, X]],
        ) -> type[OperatorGenerator[S, X]]:
            """
            Adds a generator to this decision process.

            :param cls: generator to add
            :return: added generator
            """

            self.add_generator(cls, extra, self_param)

            return cls

        return cls_dec

    def add_operator(
        self, op: Operator[S], self_param: str | None = OPERATOR_SELF_PARAM
    ) -> tuple[ActionFactory[S], Action[S], Self]:
        """
        Pass-thru to :func:`add_operator`.

        :param op: operator with factory/action info
        :param self_param: if not ``None``, action param referring to the op
        :return: the produced action factory and action, and this decision process (for chaining)
        """

        return *add_operator(self, op, self_param), self

    def add_operator_c(
        self, op: Operator[S], self_param: str | None = OPERATOR_SELF_PARAM
    ) -> Self:
        """
        Pass-thru to :meth:`DecisionProcess.add_operator`.

        :param op: operator with factory/action info
        :param self_param: if not ``None``, action param referring to the op
        :return: this decision process (for chaining)
        """

        return self.add_operator(op, self_param)[2]

    def operator(
        self,
        op_name: str,
        self_param: str | None = OPERATOR_SELF_PARAM,
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
            Adds an operator instance to this decision process.

            :param cls: operator to instantiate
            :return: added class
            """

            self.add_operator(cls(op_name, **kwargs), self_param)

            return cls

        return cls_dec

    def _terminal_check(self) -> bool:
        """
        Custom termination check, adding possibility of terminal actions
        """

        if (not self._terminated) and isinstance(self._chosen, NamedObject):
            self._terminated = TERMINAL_ACTION_ATTR in self._chosen.params

        return super()._termination_check()

    def __call__(
        self,
        max_cycles: int | None = None,
        suppress_errors: bool = True,
        args_namespace: str = ARGS_ATTR,
        **args: Any,
    ) -> S | None:
        """
        Execute the decision process, function-style

        :param max_cycles: maximum steps to execute
        :param suppress_errors: if `True`, does not raise any errors from execution
        :param args_namespace: input source name
        :param args: arguments to supply
        :return: the final state if the decision process completed
                 without any exceptions; None otherwise
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
