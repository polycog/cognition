"""
Tests for the agent skills and the plugin marketplace

* marketplace and plugin manifests parse, point at real folders,
  and the plugin version matches the library version
* every skill has frontmatter whose name matches its folder
* every ``cognition.guide "<heading>"`` reference (skills, README)
  names a real heading in the packaged agent guide
"""

import json
import re
import unittest
from pathlib import Path
from typing import Any

import cognition
from cognition.guide import guide_sections

# ===

ROOT = Path(__file__).parent.parent
"""Repository root"""

MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
"""Plugin marketplace catalog"""

SKILL_DIRS: tuple[Path, ...] = tuple(
    p
    for p in (
        *sorted((ROOT / "plugins").glob("*/skills/*")),
        *sorted((ROOT / ".claude" / "skills").glob("*")),
    )
    if p.is_dir()  # skip stray files, e.g. macOS .DS_Store
)
"""Every skill folder: plugin skills for users, project skills for contributors"""

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_GUIDE_CMD_RE = re.compile(r'cognition\.guide((?:[ \t]+"[^"\n]+")+)')
_QUOTED_RE = re.compile(r'"([^"\n]+)"')

# ===


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _frontmatter(path: Path) -> dict[str, str]:
    """Simple ``key: value`` frontmatter (single-line values only)"""

    match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if match is None:
        return {}

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()

    return fields


def _guide_references(text: str) -> list[str]:
    """Headings passed to ``python -m cognition.guide`` in the text"""

    return [
        heading
        for args in _GUIDE_CMD_RE.findall(text)
        for heading in _QUOTED_RE.findall(args)
    ]


# ===


class TestSkills(unittest.TestCase):
    """Keeps the skills and plugin metadata accurate"""

    def test_marketplace(self) -> None:
        """each catalog entry points at a plugin folder with a matching manifest"""

        catalog = _load_json(MARKETPLACE)
        self.assertTrue(catalog["plugins"])

        for entry in catalog["plugins"]:
            with self.subTest(plugin=entry["name"]):
                manifest = ROOT / entry["source"] / ".claude-plugin" / "plugin.json"
                self.assertTrue(manifest.is_file(), manifest)
                self.assertEqual(_load_json(manifest)["name"], entry["name"])

    def test_plugin_versions(self) -> None:
        """plugins are versioned in lockstep with the library"""

        for manifest in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
            with self.subTest(manifest=str(manifest.relative_to(ROOT))):
                self.assertEqual(
                    _load_json(manifest).get("version"),
                    cognition.__version__,
                    "Bump the plugin version along with cognition.__version__",
                )

    def test_skill_frontmatter(self) -> None:
        """each skill has a name (matching its folder) and a description"""

        self.assertTrue(SKILL_DIRS)

        for skill_dir in SKILL_DIRS:
            with self.subTest(skill=str(skill_dir.relative_to(ROOT))):
                fields = _frontmatter(skill_dir / "SKILL.md")
                self.assertEqual(fields.get("name"), skill_dir.name)
                self.assertTrue(fields.get("description"))
                self.assertLessEqual(len(fields["description"]), 1024)

    def test_guide_references(self) -> None:
        """every heading passed to cognition.guide exists"""

        names = {s.name for s in guide_sections()}
        files = [d / "SKILL.md" for d in SKILL_DIRS] + [ROOT / "README.md"]
        found = 0

        for path in files:
            for heading in _guide_references(path.read_text(encoding="utf-8")):
                found += 1
                with self.subTest(file=str(path.relative_to(ROOT)), heading=heading):
                    self.assertIn(heading.replace("`", ""), names)

        self.assertGreater(found, 0)
