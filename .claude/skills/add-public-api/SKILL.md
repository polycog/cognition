---
name: add-public-api
description: Checklist for adding, renaming or removing a public name (class, function, type alias, constant) in the cognition library source, so exports, the agent guide, llms.txt, docs, skills and tests stay in sync. Use when changing anything exported from src/cognition.
---

# Adding or changing public API in `cognition`

Work through every step; `source checks.sh` catches most misses, but not all.

## 1. Implement

- Follow the conventions in the repo's root `AGENTS.md`: mypy-strict typing with PEP 695 generics,
  Sphinx-style docstrings (`:param x:` / `:return:`) on everything public, a module-level
  `_logger`, `stringify(...)` for callables that show up in `str(dp)`, and `# ===` between sections.

## 2. Export it

- Add the name to its subpackage `__init__.py`: both the import and `__all__`. `development.md`
  describes the `mkinit` workflow; `type` aliases are always added by hand.
- Don't list a submodule in `__all__` if it has the same name as its subpackage (for example
  `cogent` inside `cognition.cogent`). The top-level star import would replace the subpackage
  with the inner module.
- `cognition.guide` is meta tooling and is deliberately not re-exported from the top-level
  `cognition/__init__.py`. Everything else is.

## 3. Test it

- Add tests in `tests/test_<module>.py` (`unittest`). Run one module with
  `PYTHONPATH=src python -m unittest tests.test_<module>`.

## 4. Update the agent-facing docs

- `src/cognition/AGENTS.md` (shipped in the wheel): mention the name in code (an example or an
  inline `` `span` ``), or add it to `INTENTIONALLY_OMITTED` in `tests/test_agents_md.py` with a
  reason-grouped comment. Shell commands such as `pip install ...` don't count as mentions.
  - New examples must run as-is and pass `mypy --strict`; the tests execute every `python` block.
  - If you add or rename a `##` / `###` heading, update the **Contents** list at the top.
  - If you rename a heading, update every heading passed to `python -m cognition.guide` in
    `plugins/cognition/skills/` and `README.md`; `tests/test_skills.py` checks them.
- `docs/source/_extra/llms.txt`, if the change affects a listed concept, cookbook page or example.
- The relevant page in `docs/source/ideas/` or `docs/source/cook/`.
- The skills in `plugins/cognition/skills/`, if the change affects what they tell agents to do.

## 5. Check

```bash
source checks.sh
```

If docs changed, also build them (`docs/README.md`) and look for new warnings.
