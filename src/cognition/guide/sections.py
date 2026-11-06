"""
Access to the packaged agent guide (``AGENTS.md``), one section at a time
"""

import logging
import re
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable

# ===

_logger = logging.getLogger(__name__)

# ===

_HEADING_RE = re.compile(r"^(#{1,6}) (.+?)\s*$")
_FENCE_RE = re.compile(r"^(```|~~~)")

# ===


@dataclass(frozen=True)
class GuideSection:
    """One heading of the guide and the text under it"""

    level: int
    """Heading level (1 for ``#``, 2 for ``##``, ...)"""

    heading: str
    """Heading exactly as written (may contain backticks)"""

    text: str
    """
    The heading line through the end of the section,
    including all subsections (i.e., until the next heading
    at the same or a higher level)
    """

    @property
    def name(self) -> str:
        """
        :return: heading without backticks; what to pass to
                 :func:`guide_section` (safe to quote in a shell)
        """

        return _heading_name(self.heading)


def _heading_name(heading: str) -> str:
    """
    Name used to look up a heading: the heading text without backticks
    (backticks would trigger command substitution inside shell double quotes)

    :param heading: heading as written, or a name
    :return: name for exact-match lookup
    """

    return heading.replace("`", "")


def guide_file() -> Traversable:
    """
    File path of ``AGENTS.md``

    :return: the guide shipped inside the installed ``cognition`` package
    """

    return resources.files("cognition").joinpath("AGENTS.md")


def guide_sections(text: str | None = None) -> list[GuideSection]:
    """
    Splits a markdown guide into sections, in document order.
    Lines inside fenced code blocks are never headings.

    :param text: markdown to split (``None`` for the packaged guide)
    :return: one section per heading
    """

    lines = (guide_file().read_text("utf-8") if text is None else text).splitlines(
        keepends=True
    )

    starts: list[tuple[int, int, str]] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := _HEADING_RE.match(line)):
            starts.append((i, len(m.group(1)), m.group(2)))

    sections = []
    for idx, (start, level, heading) in enumerate(starts):
        end = next(
            (s for s, lvl, _ in starts[idx + 1 :] if lvl <= level),
            len(lines),
        )
        sections.append(
            GuideSection(level, heading, "".join(lines[start:end]).rstrip() + "\n")
        )

    _logger.debug("Guide split into %s sections", len(sections))

    return sections


def guide_section(name: str, text: str | None = None) -> GuideSection:
    """
    Finds a section by exact heading match, ignoring backticks
    (see :attr:`GuideSection.name`)

    :param name: heading to find, e.g. ``"Gotchas"``
    :param text: markdown to search (``None`` for the packaged guide)
    :return: the matching section
    :raises KeyError: no heading matches (the message lists all names)
    """

    sections = guide_sections(text)
    key = _heading_name(name)

    for section in sections:
        if section.name == key:
            return section

    available = "\n".join(f"  {s.name}" for s in sections)
    raise KeyError(f"No guide heading named {name!r}. Available:\n{available}")
