"""
Guide sub-module: the packaged agent guide (AGENTS.md), by section

Not re-exported from top-level cognition (as meta tooling), so: import from cognition.guide
"""

from .sections import (
    GuideSection,
    guide_file,
    guide_section,
    guide_sections,
)

__all__ = [
    "GuideSection",
    "guide_file",
    "guide_section",
    "guide_sections",
]
