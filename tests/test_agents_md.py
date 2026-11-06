"""
Tests for the package-level agent guide (``src/cognition/AGENTS.md``)

* every ``python`` example in the guide runs (including its own asserts)
* every ``python`` example type-checks under ``mypy --strict``
* every public name is either mentioned in the guide or
  explicitly listed below as intentionally omitted
"""

import importlib
import pkgutil
import re
import sys
import tempfile
import types
import unittest
import warnings
from pathlib import Path

from mypy import api as mypy_api

import cognition

# ===

GUIDE_PATH: Path = Path(cognition.__file__).parent / "AGENTS.md"
"""Location of the guide (next to the package source, as shipped in the wheel)"""

_BLOCK_RE = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)

INTENTIONALLY_OMITTED: frozenset[str] = frozenset(
    {
        # functional type aliases
        "BiConsumer",
        "BiFunction",
        "BiPredicate",
        "Consumer",
        "Function",
        "Predicate",
        "Supplier",
        "TriFunction",
        # decision process: typing, internals, low-level helpers
        "ActionEvaluator",
        "ActionFactory",
        "ActionRank",
        "BaseDecisionProcess",
        "ChainState",
        "DecisionProcessErrorMessage",
        "DecisionProcessIterator",
        "Elaborator",
        "IO_REMOVE",
        "Link",
        "OPERATOR_SELF_PARAM",
        "Phase",
        "TERMINAL_ACTION_ATTR",
        "TerminationCheck",
        "args_added",
        "create_named_action",
        "format_name_params",
        # cogent / environment: protocols and function-style equivalents
        "Actuator",
        "ActuatorInvoker",
        "BaseActuator",
        "BaseSensor",
        "Sensor",
        "SensorReader",
        "install",
        "invoke_actuator",
        "perceive",
        "read_sensor_data",
        # knowledge: protocols, internals, linked wrappers
        "BaseSchema",
        "Fact",
        "Freezable",
        "LinkedBinaryRelation",
        "LinkedEntity",
        "Thawable",
        # language: prompt-building helpers
        "DEFAULT_SCHEMA_FIELD_NAME",
        "EmpiricalConfidence",
        "basemodel_dep_types",
        "basemodel_description",
        "basemodel_field_doc",
        "basemodel_name_doc",
        "enum_description",
        "enum_item_doc",
        "enum_name_doc",
        "enum_schema",
        # reasoning: search internals
        "FrontierManager",
        "FrontierNode",
        "PathCost",
        "SearchState",
        "Succession",
        # util
        "AttrReferral",
        "EnumDispatch",
        "ImplementsLessThan",
        "MutableWrapper",
        "StringifiedFunction",
        "TypedMixin",
        "is_list",
        "is_set",
        "optionally_name",
        "timed",
    }
)
"""
Public names deliberately left out of the guide.

A new public name must either be mentioned in the guide or added here,
so that every API addition is a conscious documentation decision.
"""

# ===


def _guide_text() -> str:
    return GUIDE_PATH.read_text(encoding="utf-8")


def _python_blocks() -> list[str]:
    return _BLOCK_RE.findall(_guide_text())


def _public_names() -> set[str]:
    """Non-module names exported via each subpackage's ``__all__``"""

    names: set[str] = set()

    for info in pkgutil.iter_modules(cognition.__path__):
        sub = importlib.import_module(f"{cognition.__name__}.{info.name}")

        for name in getattr(sub, "__all__", ()):
            if not isinstance(getattr(sub, name), types.ModuleType):
                names.add(name)

    return names


_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_SHELL_SPAN_RE = re.compile(r"^(pip|python|uv)\s")


def _code_text(text: str) -> str:
    """
    Only code counts as a mention (fenced blocks + inline `spans`),
    so prose words like "perceive" or "Phase" don't match API names;
    shell commands are skipped, so `pip install ...` doesn't count as `install`
    """

    spans = [s for s in _INLINE_CODE_RE.findall(text) if not _SHELL_SPAN_RE.match(s)]
    return "\n".join(_BLOCK_RE.findall(text) + spans)


def _mentioned(name: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(name)}\b", _code_text(text)) is not None


_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_HEADING_RE = re.compile(r"^(##|###) (.+)$", re.MULTILINE)
_CONTENTS_RE = re.compile(r"^\*\*Contents\*\*\n\n((?:- .+\n)+)", re.MULTILINE)


def _expected_contents(text: str) -> list[str]:
    """
    One line per ## heading, listing its ### headings
    (code blocks removed first: their comments start with #)
    """

    sections: list[tuple[str, list[str]]] = []

    for level, title in _HEADING_RE.findall(_FENCE_RE.sub("", text)):
        if level == "##":
            sections.append((title, []))
        else:
            sections[-1][1].append(title)

    return [f"- {h2}" + (": " + " · ".join(h3s) if h3s else "") for h2, h3s in sections]


# ===


class TestAgentsGuide(unittest.TestCase):
    """Keeps src/cognition/AGENTS.md accurate and complete"""

    maxDiff = None  # show the full Contents diff on failure

    def test_guide_present(self) -> None:
        """the guide exists and contains examples"""

        self.assertTrue(GUIDE_PATH.is_file(), GUIDE_PATH)
        self.assertGreater(len(_python_blocks()), 0)

    def test_examples_run(self) -> None:
        """each example runs in its own fresh module"""

        for i, code in enumerate(_python_blocks()):
            with self.subTest(block=i, first_line=code.splitlines()[0]):
                mod_name = f"_agents_md_block_{i:02d}"
                module = types.ModuleType(mod_name)

                # registered so dataclasses/pydantic can resolve the module
                sys.modules[mod_name] = module
                try:
                    with warnings.catch_warnings():
                        # pydantic_graph (via Pydantic AI's run_sync) calls
                        # asyncio.get_event_loop() with no loop: harmless, Python 3.13 only
                        warnings.filterwarnings(
                            "ignore",
                            message="There is no current event loop",
                            category=DeprecationWarning,
                        )
                        exec(  # noqa: S102  # pylint: disable=exec-used
                            compile(code, f"{GUIDE_PATH}[block {i}]", "exec"),
                            module.__dict__,
                        )
                finally:
                    del sys.modules[mod_name]

    def test_examples_typecheck(self) -> None:
        """each example passes mypy --strict (as a separate module)"""

        with tempfile.TemporaryDirectory() as tmp:
            files: list[str] = []

            for i, code in enumerate(_python_blocks()):
                path = Path(tmp) / f"agents_md_block_{i:02d}.py"
                path.write_text(code, encoding="utf-8")
                files.append(str(path))

            # pylint: disable-next=c-extension-no-member
            stdout, stderr, status = mypy_api.run(
                [
                    "--strict",
                    "--no-error-summary",
                    "--cache-dir",
                    str(Path(tmp) / ".mypy_cache"),
                    *files,
                ]
            )

            self.assertEqual(status, 0, stdout + stderr)

    def test_contents_match_headings(self) -> None:
        """the Contents list matches the guide's actual section headings"""

        text = _guide_text()
        match = _CONTENTS_RE.search(text)

        self.assertIsNotNone(match, "Contents list not found")
        assert match is not None  # for type checking

        self.assertEqual(
            match.group(1).splitlines(),
            _expected_contents(text),
            "Update the Contents list in src/cognition/AGENTS.md to match its headings",
        )

    def test_public_names_covered(self) -> None:
        """every public name is documented or deliberately omitted"""

        text = _guide_text()
        undocumented = sorted(
            name
            for name in _public_names() - INTENTIONALLY_OMITTED
            if not _mentioned(name, text)
        )

        self.assertFalse(
            undocumented,
            "Mention in src/cognition/AGENTS.md, "
            f"or add to INTENTIONALLY_OMITTED: {undocumented}",
        )

    def test_omitted_list_current(self) -> None:
        """the omitted list contains no removed or now-documented names"""

        text = _guide_text()

        self.assertFalse(
            sorted(INTENTIONALLY_OMITTED - _public_names()),
            "No longer public; remove from INTENTIONALLY_OMITTED",
        )
        self.assertFalse(
            sorted(n for n in INTENTIONALLY_OMITTED if _mentioned(n, text)),
            "Now mentioned in the guide; remove from INTENTIONALLY_OMITTED",
        )


if __name__ == "__main__":
    unittest.main()
