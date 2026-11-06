"""
Tests for section access to the packaged agent guide
"""

import contextlib
import io
import subprocess
import sys
import unittest

from cognition.guide import GuideSection, guide_section, guide_sections
from cognition.guide.__main__ import main

# ===

_SAMPLE = """# Title

intro

## First `thing`

one

```python
# not a heading
```

### Sub A

a

### Sub B

b

## Second

two
"""

# ===


def _run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = main(list(argv))
    return status, out.getvalue(), err.getvalue()


class TestGuide(unittest.TestCase):
    """Tests for cognition.guide"""

    def test_sections(self) -> None:
        """headings in code fences are skipped; sections nest by level"""

        sections = guide_sections(_SAMPLE)

        self.assertEqual(
            [(s.level, s.heading) for s in sections],
            [
                (1, "Title"),
                (2, "First `thing`"),
                (3, "Sub A"),
                (3, "Sub B"),
                (2, "Second"),
            ],
        )

        self.assertEqual(sections[0].text, _SAMPLE)
        self.assertIn("### Sub B", sections[1].text)
        self.assertNotIn("## Second", sections[1].text)
        self.assertEqual(sections[2].text, "### Sub A\n\na\n")
        self.assertEqual(sections[4].text, "## Second\n\ntwo\n")

    def test_lookup(self) -> None:
        """exact match, backticks optional on either side"""

        for name in ("First thing", "First `thing`"):
            section = guide_section(name, _SAMPLE)
            self.assertIsInstance(section, GuideSection)
            self.assertEqual(section.heading, "First `thing`")
            self.assertEqual(section.name, "First thing")

        for name in ("first thing", "First", "Sub", "not a heading"):
            with self.assertRaises(KeyError) as ctx:
                guide_section(name, _SAMPLE)
            self.assertIn("Sub A", str(ctx.exception))

    def test_packaged_guide(self) -> None:
        """the real guide parses, and every name is unique (so lookups are unambiguous)"""

        names = [s.name for s in guide_sections()]

        self.assertIn("Gotchas", names)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all("`" not in n for n in names))
        self.assertTrue(guide_section("Gotchas").text.startswith("## Gotchas\n"))

    def test_cli(self) -> None:
        """list, print, path, unknown heading"""

        status, out, _ = _run()
        self.assertEqual(status, 0)
        self.assertIn("\n  Gotchas\n", out)
        self.assertIn("\n    The cogent loop\n", out)

        status, out, _ = _run("Gotchas", "Debugging")
        self.assertEqual(status, 0)
        self.assertTrue(out.startswith("## Gotchas\n"))
        self.assertIn("\n## Debugging\n", out)

        status, out, _ = _run("--path")
        self.assertEqual(status, 0)
        self.assertTrue(out.strip().endswith("AGENTS.md"))

        status, out, err = _run("Nope")
        self.assertEqual(status, 1)
        self.assertEqual(out, "")
        self.assertIn("Available:", err)

    def test_module_entry_point(self) -> None:
        """`python -m cognition.guide` runs cleanly (no runpy warnings)"""

        result = subprocess.run(
            [sys.executable, "-W", "error", "-m", "cognition.guide", "Gotchas"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## Gotchas\n"))
