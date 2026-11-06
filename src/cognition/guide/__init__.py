"""
Guide sub-module: the packaged agent guide (AGENTS.md), by section

Since meta, not exporting quite so much
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
