"""
Example choice container: a set of clothing
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import override

from cognition import AutoDocEnum, Predicate

from container import ChoiceContainer

# ===


class Hat(AutoDocEnum):
    """hat options"""

    NONE = "👦"
    FUN = "🤠"
    CAP = "🧢"


class Clothing(AutoDocEnum):
    """clothing options"""

    COMFORTABLE = "☺️"
    FANCY = "🤵"


class ColorPalette(AutoDocEnum):
    """color palette options"""

    NEUTRAL = "😴"
    VIBRANT = "🤩"


# ===


@dataclass
class Outfit(ChoiceContainer):
    """Choices to produce an outfit"""

    hat: Hat | None = None
    clothing: Clothing | None = None
    colors: ColorPalette | None = None

    # ===

    @override
    @property
    def _acceptable(self) -> bool:

        # silly example constraints
        _bad_checks: Iterable[Predicate[Outfit]] = (
            # don't where a baseball cap with fanciness
            lambda o: o.clothing == Clothing.FANCY and o.hat == Hat.CAP,
            # a vibrant outfit DEMANDS a hat
            lambda o: o.colors == ColorPalette.VIBRANT and o.hat == Hat.NONE,
            # neutral colors == 😭
            lambda o: o.colors == ColorPalette.NEUTRAL,
        )

        bad_outfit = any(bc(self) for bc in _bad_checks)

        return not bad_outfit
