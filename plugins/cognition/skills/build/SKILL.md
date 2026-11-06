---
name: build
description: Write or change Python code that uses the cognition library (PyPI polycog-cognition) to build neurosymbolic agents, e.g. DecisionProcess, Operator, evaluators, StagedState, Cogent with sensors and actuators, SearchPlanner, WorldGraph, EnumClassifier or ModelPopulator. Use whenever code imports cognition or the user wants to build an agent with it.
---

# Building with `cognition`

The library's agent guide ships inside the installed package and matches its version. Read the
relevant sections from it before writing code; don't rely on memory of the API.

## 1. Check the library is available

```bash
python -m cognition.guide
```

This lists the guide's headings. If it fails with `No module named 'cognition'`, the library isn't
installed in the active Python environment. Use the project's environment (venv, uv, poetry, ...)
or ask the user before installing `polycog-cognition`. If it can't be installed yet, read
<https://docs.polycog.ai/AGENTS.md> instead (it matches the latest release, not necessarily the
version the project will use).

## 2. Always read these first

```bash
python -m cognition.guide "Mental model" "Gotchas"
```

The core design rule: deterministic Python (decision processes, planners) owns control flow, and
LLMs only translate between natural language and typed data.

## 3. Read the sections for the task

Pass several headings to one command. Headings must match exactly; backticks are optional.

| Task | Sections |
|---|---|
| Rules, actions, termination, run arguments | `"Operators, arguments, terminal actions"` |
| Several valid actions, preferences | `"Competing actions and preferences (evaluators)"`, `"Propose everything that's valid; let evaluators choose"` |
| A workflow driven by one enum field | `"Staged workflows"` |
| An agent loop with real input and output | `"The cogent loop"`, `"Agents: sensors, actuators and the cogent loop"` |
| State kept across runs or loop iterations | `"State that survives reinit, plus self-elaboration"` |
| Finding an action sequence to reach a goal | `"Planning with search"`, `"Planning: options mirror operators, and snapshots make good planner states"` |
| Typed facts and relations | `"Knowledge: typed facts and a world graph"` |
| Classifying, extracting or describing with an LLM | `"Language: LLMs into and out of typed data"`, `"Do expensive work once, in perform"` |
| A complete small agent to start from | `"Putting it together: a ticket router"` |
| Laying out files for a new or growing agent | `"Organize code by kind of task knowledge"`, `"Keep operators small; decompose with elaboration and sub-DPs"` |
| Choosing between returning and mutating state | `"Pick a state style: functional or imperative"` |

Before finishing, also read `"Anti-patterns"` and check the code against it.

## 4. Verify

- Run new decision processes with `dp(suppress_errors=False, max_cycles=...)` while developing, so
  errors raise instead of returning `None` and a missing termination can't hang.
- Test LLM-backed code offline with Pydantic AI's `TestModel` or `FunctionModel`, as the Language
  section shows.
- For a structured review, use the `review` skill. If a run misbehaves, use the `debug` skill.
