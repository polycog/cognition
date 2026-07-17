"""
Support for task flow housed
within a single enumerated field.
"""

from typing import Any, Optional, cast

from collections.abc import Mapping

from enum import Enum

from dataclasses import dataclass

from ..util.functypes import BiFunction, Function

from ..util.enumeration import EnumDispatch

from ..decision.core import IOContainer

from ..decision.enhancements import EnhancedTask, NamedOperator

#


@dataclass
class StagedState[T: Enum](EnumDispatch[T]):
    """
    Extensible state with an
    enumerated stage controlled
    via enum-named transition

    To use...

    * declare @dataclass subclass with
      stage field type and initial value
    * add additional fields as necessary
    * implement enum-named methods for non-
      terminal stages; each of which must
      return the next stage value (and can
      take arbitrary supporting arguments)
    """

    stage: T
    """
    Required field: locus of task-flow state
    """

    def transition(self, *args: Any, **kwargs: Any) -> None:
        """
        Update stage via enum-named methods;
        each such method must return
        the next stage, with logic dependent
        upon passed arguments.

        :param args: positional arguments to pass
        :param kwargs: keyword arguments to pass
        """

        next_stage = self(self.stage, *args, **kwargs)
        if next_stage is not None:
            self.stage = cast(T, next_stage)


type KWArgs = Mapping[str, Any]
"""Shorthand for kwarg_name=kwarg_value"""

# pylint: disable=line-too-long
type StageSupporter[E: Enum, S: StagedState[E]] = BiFunction[S, IOContainer, Optional[KWArgs]]  # type: ignore
"""Function to optionally provide kwargs based upon interaction with IO"""


def staged_operator[SE: Enum, SS: StagedState[SE]](  # type: ignore[name-defined]
    t: EnhancedTask[SS], stage: SE, **kwargs: Any
) -> Function[StageSupporter[SE, SS], StageSupporter[SE, SS]]:
    """
    Given that a task is using a staged state,
    convenience decorator to add a full
    operator that applies during a supplied stage

    :param t: task to add operator to
    :param stage: stage when added operator should apply
    :param kwargs: operator params
    """

    def _decorator(ss: StageSupporter[SE, SS]) -> StageSupporter[SE, SS]:

        @t.operator(stage.name, **kwargs)
        class _StagedOperator(NamedOperator[SS]):

            def can_perform(self, state: SS, _io: IOContainer) -> bool:
                return state.stage == stage

            def perform(self, state: SS, io: IOContainer) -> None:
                kwargs = ss(state, io)
                if kwargs is None:
                    kwargs = {}

                state.transition(**kwargs)

        return ss

    return _decorator
