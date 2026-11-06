# AGENTS.md

Guidance for AI coding agents working **on** this repository. If you are writing an app that
*uses* the library, read [`src/cognition/AGENTS.md`](src/cognition/AGENTS.md) instead.

## Project

- `polycog-cognition` on PyPI; import name `cognition`. Python >= 3.13.
- Source lives in `src/cognition/`; tests in `tests/` (`unittest`, one `test_<module>.py` per module).
- Docs live in `docs/` (Sphinx + MyST + sphinx-autoapi), and the cookbook code is in `docs/source/cook/src/`.
  Runnable example apps are in `examples/`.
- Agent-facing material: the usage guide `src/cognition/AGENTS.md` (read by section via
  `python -m cognition.guide`), user skills in the plugin `plugins/cognition/`
  (catalog: `.claude-plugin/marketplace.json`), and contributor skills in `.claude/skills/`.

## Setup and checks

```bash
python -m venv venv && source venv/bin/activate
pip install -r dev-requirements.txt   # includes `-e .`
source checks.sh                      # must pass before committing
```

`checks.sh` runs, in order: `mypy tests src` (strict), `pylint tests src`, `ruff check tests src`,
`black --check tests src`, `validate-pyproject`, `cffconvert --validate`, and unit tests under
`coverage`. To run one test module: `PYTHONPATH=src python -m unittest tests.test_dp`.

CI is defined in `.github/workflows/`. `checks.yml` runs `source checks.sh` on every push and PR to
`main` across Python 3.13–3.15, so a local pass of `checks.sh` is the CI gate. If you change the
tooling (`checks.sh`, `dev-requirements.txt`, supported Python versions), keep the workflows consistent.

## Conventions

- Fully typed (mypy strict) using PEP 695 generics (`class Foo[S]:`, `type Alias[T] = ...`).
- Sphinx-style docstrings (`:param x:` / `:return:`) on all public API. autoapi renders them as the API reference.
- Each module has a module-level `_logger = logging.getLogger(__name__)`. Log at `info` for lifecycle events
  and at `debug` for details. Never configure handlers inside the library.
- Use `stringify(...)` so callables have a readable `str()`, because `str(dp)` is a primary debugging tool.
- Sections within a module are separated by `# ===`.
- Public names are re-exported by hand through each subpackage's `__init__.py` (imports + `__all__`),
  and from there through `cognition/__init__.py`. See `development.md` for the `mkinit` workflow. A new public
  name must be added to its subpackage `__init__`. Note that `type` aliases are always added manually.
  Also note that meta tooling (`guide`) is intentionally NOT re-exported.
- The version is `__version__` in `src/cognition/__init__.py` (setuptools reads it dynamically).

## When you change the public API

Keep the downstream guidance in sync:
- `src/cognition/AGENTS.md` (shipped inside the wheel)
- `docs/source/_extra/llms.txt` (published at docs.polycog.ai/llms.txt)
- the relevant page in `docs/source/ideas/` or `docs/source/cook/`
- the user-facing skills in `plugins/cognition/skills/` (they name guide headings, which
  `tests/test_skills.py` checks exist)

The project skill `.claude/skills/add-public-api/` walks through these steps.

## Releases

Publishing a GitHub release triggers both the PyPI upload (`.github/workflows/pypi.yml`) and the docs
build/deploy (`.github/workflows/docs.yml`). The docs workflow can also be run by hand between
releases for small fixes (e.g., typos): `gh workflow run docs.yml --ref <branch>`. A manual run
publishes the docs *at that ref*, so running it from `main` also publishes any docs or API changes
that haven't been released yet. Don't trigger either workflow without being asked.

The plugin (`plugins/cognition/`, listed in `.claude-plugin/marketplace.json`) is versioned in 
lockstep with the library: bump `version` in `plugins/cognition/.claude-plugin/plugin.json`
along with `__version__` (`tests/test_skills.py` enforces this). Installed plugins only update when
that version changes, so skill fixes reach users at the next release.
