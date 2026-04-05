"""
Practical library additions
"""

from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Optional,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    runtime_checkable
)

from enum import IntEnum

from functools import wraps

from cognition.functypes import (
    BiFunction,
    Predicate,
)

from cognition.utility import ImplementsLessThan

from cognition.core import (
    Action,
    ActionEvaluator,
    ActionRank,
    Elaborator,
    IOContainer,
)

#

class Rank(IntEnum):
    """
    Simple ordering of possible
    rankings of actions to pursue;
    sorting is used, so lower
    numbers are more important
    """

    HIGH = 1
    MEDIUM = 2
    LOW = 3


P = ParamSpec("P")
R = TypeVar("R")

class StringifiedFunction(Generic[P, R]):
    """
    A callable object that wraps a function
    and provides a custom __str__ representation.
    """

    def __init__(self, func: Callable[P, R], str_representation: str):
        """
        Wrapping function and __str__
        representation
        """

        wraps(func)(self)
        self._func: Callable[P, R] = func
        self._str_representation: str = str_representation

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Calls the original function
        """
        return self._func(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns the custom string representation
        """

        return self._str_representation

def stringify(str_representation: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for stringifying
    a function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return StringifiedFunction(func, str_representation)

    return decorator


def create_elaborator[S](
    name: Optional[str] = None,
    **kwargs: BiFunction[S, IOContainer, Any]
) -> Elaborator[S]:
    """
    Produces an (optionally named)
    elaborator given association
    between keywords and functions
    """

    def _f(s: S, io: IOContainer) -> dict[str, Any]:
        return {
            k: v(s, io)
            for k, v in kwargs.items()
        }

    if name:
        return stringify(name)(_f)

    return _f


# pylint: disable=too-few-public-methods
@runtime_checkable
class NamedAction(Protocol):
    """
    Represents an action
    that has been augmented
    with some annotation
    """

    name: str
    params: Mapping[str, Any]

def create_named_action[S](
    name: str,
    f: Action[S],
    **kwargs: Any
) -> Action[S]:
    """
    Produces a function that has
    a nice __str__ and access to
    name via f.name and kwargs 
    via f.params
    """

    def qualified_name() -> str:
        if kwargs:
            params_str = ", ".join(f"{k}={repr(v)}" for k,v in kwargs.items())
            return f"{name}[{params_str}]"

        return name

    new_f = stringify(qualified_name())(f)

    # pylint: disable=attribute-defined-outside-init
    new_named = cast(NamedAction, new_f)
    new_named.name = name
    new_named.params = kwargs.copy()

    return new_f


def uniform_evaluator[S](
        r: ImplementsLessThan,
        p: Predicate[Action[S]] = lambda _: True,
        name: Optional[str] = None
    ) -> ActionEvaluator[S]:
    """
    Produces a convenience ActionEvaluator 
    that applies a supplied rank to all 
    potential actions that satisfy a predicate
    """

    def evaluation_func(
        _state: S,
        _io: IOContainer,
        potential_actions: Iterable[Action[S]]
    ) -> Iterable[ActionRank[S]]:
        return (ActionRank(a, r) for a in potential_actions if p(a))

    if name:
        return stringify(name)(evaluation_func)

    return evaluation_func
