"""
Re-usable state components
"""

import logging
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Self, final, override

from ..util.functypes import Supplier
from ..util.misc import AttrReferral, stringify
from .core import Elaborator, IOContainer

# ===

_logger = logging.getLogger(__name__)

# ===


# pylint: disable=too-few-public-methods
class SelfReinitState:
    """
    State that internally handles reinitialization.

    Supply a subclass instance to a decision process
    as a ``state_initializer`` and the result will be
    internal control about dp reinit.
    """

    def _reinit(self) -> None:
        """Override to implement custom reinit logic"""

    @final
    def __call__(self) -> Self:
        _logger.info(
            "%s %s: reinit called", SelfReinitState.__name__, type(self).__name__
        )

        self._reinit()
        return self


# pylint: disable=too-few-public-methods
class SelfElaborationState(SelfReinitState):
    """
    State that self-serves elaboration.

    A decision process that uses an instance's
    :attr:`elaborator` property will provide it an
    opportunity for elaboration (during the phase),
    whose read-only results are then accessible
    via a protected property (that can then be
    exposed via state-designer preference).
    """

    ELABORATOR_NAME: str = "self_elab"
    """Name of the resulting elaborator"""

    # pylint: disable=attribute-defined-outside-init
    def __init_elab(self) -> None:
        try:
            _ = self.__elab_values
        except AttributeError:
            self.__elab_values: dict[str, Any] = {}
            self.__elab_view = MappingProxyType(self.__elab_values)

    @final
    @property
    def elaborator(self) -> Elaborator[Self]:
        """
        :return: fixed elaborator for this instance
        """

        self.__init_elab()

        @stringify(f"{SelfElaborationState.ELABORATOR_NAME}({type(self).__name__})")
        def _elaborator(_: Self, io: IOContainer) -> dict[str, Any]:

            _logger.info(
                "%s %s: (self-)elaborate",
                SelfElaborationState.__name__,
                type(self).__name__,
            )

            self.__elab_values.clear()

            new_elab = self._elaborate(io)
            _logger.debug(
                "%s %s: (i=%s, o=%s) -> %s",
                SelfElaborationState.__name__,
                self,
                {k: str(v) for k, v in io.input.items()},
                {k: str(v) for k, v in io.output.items()},
                new_elab,
            )

            self.__elab_values.update(new_elab)
            return {}

        return _elaborator

    @override
    def _reinit(self) -> None:
        self.__init_elab()
        self.__elab_values.clear()

    # pylint: disable=unused-argument
    def _elaborate(self, io: IOContainer) -> Mapping[str, Any]:
        """
        Override to implement custom elaboration logic

        :param io: access to current IO
        :return: name=value set for current elaboration
        """

        return {}

    @final
    @property
    def _elab_values(self) -> MappingProxyType[str, Any]:
        """
        :return: read-only access to elaborated values
        """

        self.__init_elab()
        return self.__elab_view


class PTEState[P, T](SelfElaborationState):
    """
    Container for state that...

    * is (P)ersistant across dp reinitialization;
    * is (T)ransient, and so is reset each dp reinit; and
    * is (E)laborated each cycle based upon P/T state + IO
      via a custom implementation of `_elaborate`
    """

    def __init__(self, p_init_value: P, t_init: Supplier[T]) -> None:
        """
        :param p_init_value: initial value of persistent state
        :param t_init: function to (re)initialize transient state
        """

        _logger.info(
            "%s %s: initialize",
            PTEState.__name__,
            type(self).__name__,
        )

        self._p = p_init_value
        self._t_init = t_init

        self._e = AttrReferral(self._elab_values)

        self._reinit()

        _logger.debug(
            "%s %s: (p_init=%s, t_init=%s) -> %s",
            PTEState.__name__,
            type(self).__name__,
            p_init_value,
            t_init,
            self,
        )

    @override
    def _reinit(self) -> None:
        super()._reinit()
        self._t = self._t_init()

    # ===

    @property
    def p(self) -> P:
        """
        :return: persistent state
        """

        return self._p

    @property
    def t(self) -> T:
        """
        :return: transient state
        """

        return self._t

    @property
    def e(self) -> AttrReferral:
        """
        :return: elaborated state
        """

        return self._e

    def __str__(self) -> str:
        return f"{type(self).__name__}(p={self._p}; t={self._t}; e={self._elab_values})"


class PEState[P](PTEState[P, None]):
    """
    Convenience special case of :class:`PTEState`
    whose transient state is ``None``
    """

    @stringify("return_none")
    @staticmethod
    def __t_init_none() -> None: ...

    def __init__(self, p_init_value: P) -> None:
        """
        :param p_init_value: initial value of persistent state
        """

        super().__init__(p_init_value, PEState.__t_init_none)
