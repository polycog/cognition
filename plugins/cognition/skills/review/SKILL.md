---
name: review
description: Review Python code that uses the cognition library (polycog-cognition) against its idioms, anti-patterns and gotchas, e.g. side effects in can_perform, LLMs driving control flow, missing evaluators or termination. Use when asked to review, audit or check cognition-based code, or after writing a substantial decision process or cogent.
---

# Reviewing `cognition` code

## 1. Load the rules for the installed version

```bash
python -m cognition.guide "Anti-patterns" "Idioms" "Gotchas"
```

If `cognition` isn't importable, see step 1 of the `build` skill.

## 2. Inventory the knowledge

For each `DecisionProcess` (and each `Cogent`), list where its parts are defined: state type,
elaborators, termination checks, operators and generators, evaluators, sensors and actuators, and
any sub-DPs, planners or language helpers it calls. Review each part in its own context.

## 3. Check each part

Cite the guide section for every finding. Check at least:

- **`can_perform`, elaborators, termination checks, evaluators** only read. Reading `io.i`, `io.a`
  and `io.e` is expected; changing state, writing to `io.o` (actuators, `io.o.log`), external I/O
  (network, files, databases) and LLM or planner calls are not (`"Anti-patterns"`,
  `"Do expensive work once, in perform"`).
- **`perform`** does one step: no long loops or hidden multi-step logic, and it returns `None`
  unless it deliberately replaces the state (`"Anti-patterns"`, `"Gotchas"`).
- **Preferences** live in evaluators, not in mutually exclusive `can_perform` conditions, and every
  action that can compete with another is ranked by some evaluator
  (`"Propose everything that's valid; let evaluators choose"`).
- **Termination** is reachable: every non-final state has an applicable operator, and each ending
  condition is either a `terminal` operator or a termination check, not both
  (`"The decision process cycle"`, `"Gotchas"`).
- **LLM output** is turned into typed values, checked (`None`, confidence) and stored in state or
  run arguments; it never chooses which operator runs (`"Anti-patterns"`,
  `"Language: LLMs into and out of typed data"`).
- **State** is typed, not free-form text, and anything that must survive `reinit` or cogent loop
  iterations is kept appropriately (`"State that survives reinit, plus self-elaboration"`).
- **Planner states** are immutable and hashable, and options never mutate their input
  (`"Planning: options mirror operators, and snapshots make good planner states"`).
- **Async code** calls the language helpers through `asyncio.to_thread` (`"Gotchas"`).

## 4. Run it

If there are tests or an entry point, run them. Rerun decision processes with
`suppress_errors=False` and a `max_cycles` limit so hidden errors surface.

## 5. Report

List findings most serious first. For each: file and line, the guide section it relates to, what
goes wrong (a concrete input or state if possible) and a suggested fix. Keep style suggestions
separate from correctness problems.
