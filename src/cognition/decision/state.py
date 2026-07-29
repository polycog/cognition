"""
Re-usable state components
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Self, final

from ..util.misc import stringify
from .core import Elaborator, IOContainer

# ===


# pylint: disable=too-few-public-methods
class SelfReinitState:
    """
    State that internally handles reinitialization.

    Supply a subclass instance to a decision process
    as a `state_initializer` and the result will be
    internal control about dp reinit.
    """

    def _reinit(self) -> None:
        """Override to implement custom reinit logic"""

    @final
    def __call__(self) -> Self:
        self._reinit()
        return self


# pylint: disable=too-few-public-methods
class SelfElaborationState:
    """
    State that self-serves elaboration.

    A decision process that uses an instance's
    `elaborator` property will provide it an
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
            self.__elab_values.clear()
            self.__elab_values.update(self._elaborate(io))
            return {}

        return _elaborator

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
