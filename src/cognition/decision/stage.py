"""
Support for workflow housed
within a single enumerated field.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from ..decision.core import IOContainer
from ..decision.dp import DecisionProcess, Operator
from ..util.enumeration import EnumDispatch
from ..util.functypes import BiFunction, Function

# ===

_logger = logging.getLogger(__name__)

# ===


@dataclass
class StagedState[T: Enum](EnumDispatch[T]):
    """
    Extensible state with an
    enumerated stage controlled
    via enum-named transition

    To use...

    * declare :func:`dataclasses.dataclass` subclass with
      ``stage`` field type and initial value
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

        _logger.debug(
            "%s %s: transition (stage=%s, args=%s, kwargs=%s)",
            StagedState.__name__,
            self,
            self.stage,
            args,
            kwargs,
        )

        next_stage = self.dispatch(self.stage, *args, **kwargs)

        _logger.info(
            "%s %s: stage=%s -> stage=%s",
            StagedState.__name__,
            type(self).__name__,
            self.stage,
            next_stage if next_stage is not None else f"{next_stage} (no change)",
        )

        if next_stage is not None:
            self.stage = cast(T, next_stage)


# pylint: disable=line-too-long
type StageSupporter[E: Enum, S: StagedState[E]] = BiFunction[S, IOContainer, Mapping[str, Any] | None]  # type: ignore
"""Function to optionally provide kwargs based upon interaction with IO"""


def staged_operator[SE: Enum, SS: StagedState[SE]](  # type: ignore[name-defined]
    dp: DecisionProcess[SS], stage: SE, **kwargs: Any
) -> Function[StageSupporter[SE, SS], StageSupporter[SE, SS]]:
    """
    Given that a decision process is using a staged
    state, convenience decorator to add a full
    operator that applies during a supplied stage

    :param dp: decision process to add operator to
    :param stage: stage when added operator should apply
    :param kwargs: operator params
    """

    def _decorator(ss: StageSupporter[SE, SS]) -> StageSupporter[SE, SS]:

        @dp.operator(stage.name, **kwargs)
        class _StagedOperator(Operator[SS]):

            def can_perform(self, state: SS, _io: IOContainer) -> bool:
                return state.stage == stage

            def perform(self, state: SS, io: IOContainer) -> None:

                _logger.debug(
                    "%s: state=%s, supporter=%s, i=%s, o=%s",
                    _StagedOperator.__name__,
                    state.stage,
                    ss,
                    {k: str(v) for k, v in io.input.items()},
                    {k: str(v) for k, v in io.output.items()},
                )

                kwargs = ss(state, io)
                if kwargs is None:
                    kwargs = {}

                _logger.debug(
                    "%s: kwargs from supporter=%s", _StagedOperator.__name__, kwargs
                )

                state.transition(**kwargs)

        return ss

    return _decorator
