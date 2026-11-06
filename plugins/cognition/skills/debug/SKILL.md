---
name: debug
description: Diagnose a cognition (polycog-cognition) DecisionProcess or Cogent that returns None, never finishes, raises DecisionProcessExecutionError (NO_PROPOSAL or NO_RANK), picks the wrong action, or ends up with an unexpected state. Use when code built with the cognition library misbehaves at runtime.
---

# Debugging `cognition` code

## 1. Load the relevant guide sections

```bash
python -m cognition.guide "Gotchas" "Debugging" "The decision process cycle"
```

For a `Cogent`, add `"The cogent loop"`. If `cognition` isn't importable, see step 1 of the
`build` skill.

## 2. Make the failure visible

`dp()` hides errors by default. Reproduce with:

```python
final = dp(suppress_errors=False, max_cycles=50)  # raises instead of returning None; can't hang
print(dp.done, dp.num_cycles)
print(dp)  # phase, state, chosen action, proposals, rankings, registered components
```

For a `Cogent`, call it with `max_cycles=...` and without `dp_err_p` / `other_err_p`, so errors
propagate. For more detail, enable logging:
`logging.basicConfig(); logging.getLogger("cognition").setLevel(logging.INFO)`.

## 3. Match the symptom

| Symptom | Likely cause | Check |
|---|---|---|
| `dp()` returns `None` | An exception was swallowed, or `max_cycles` ran out | Rerun as in step 2; check `dp.done` |
| Never finishes | No termination check or `terminal` operator ever fires | Step with `dp.run_cycles(1)` and print the state each cycle |
| `NO_PROPOSAL` | A non-final state has no applicable operator | `print(dp)` at the failure; check each operator's `can_perform` against that state |
| `NO_RANK` | Several proposals, and no evaluator ranked any of them | Add an evaluator, or make an existing one cover these actions |
| Wrong or varying action | Ties at the best rank are broken at random, or a preference is missing | Read the rankings in `print(dp)` |
| State turned into `True` or another odd value | An action returned a value, which replaces the state | Make `perform` return `None` when it mutates in place |
| Second run returns the old result | A finished DP stays finished | Call `dp.reinit()` before running again |
| `io.e` value missing, or self-elaboration not running | `io.e` is cleared each cycle, or the DP was built from a factory instead of a state instance | See the `"Gotchas"` entries on elaboration |
| Classifier returns `None` with high confidence | Called inside a running event loop | Use `await asyncio.to_thread(...)` |

To step manually, use `dp.run_phase()`, `dp.run_cycles(n)`, or iterate `dp.cycles()` /
`dp.phases()`, and inspect `dp.chosen_action` and `dp.io` along the way. Wrap your own lambdas with
`stringify("name")(fn)` so they print readably.

## 4. Fix and lock it in

Fix the cause, not the symptom (e.g., add the missing operator rather than a broad termination
check). Then add a test that reproduces the original failure, running the DP with
`suppress_errors=False`.
