# AGENTS.md

Guidance for coding agents helping developers build applications **with** `cognition` (PyPI: `polycog-cognition`), Polycog's neurosymbolic agent framework.

> Contributing to the library itself? See [development.md](development.md) for the dev workflow and pre-commit checks.

## Install & Requirements

- Python >= 3.13
- `pip install polycog-cognition`
- The package is fully typed (`py.typed`); generated code should type-check under `mypy --strict`.
- Everything is re-exported from the top-level package: `from cognition import Cogent, DecisionProcess, ...`

## Mental Model

Build agents by keeping control flow deterministic and declarative, and use LLMs only for narrow, contract-bound language tasks.

| Concept | Where | Role | Agentic-AI analogue |
|---|---|---|---|
| `Cogent` | `cognition.cogent` | (Cog)nitive ag(ent) runtime loop; tooling via sensors/actuators | Harness |
| `DecisionProcess` (DP) | `cognition.decision` | State-driven operator selection | Orchestrator / workflows |

The root DP of a cogent interacts with sensors & actuators, as well as read-only arguments, via an `IOContainer`.

The cogent loop is as follows...
1. Reinitialize the DP; load run arguments
2. Repeat
   1. Snapshot all current sensor values into the decision process IOContainer
   2. Run DP until termination, cycle limit, or error
   3. Check cogent gating predicate (exit if repeat predicate is not satisfied)


DP state can be an arbitrary type, but complex agents may benefit from the scaling, flexibility, and (queryable) structure of a knowledge graph...

| Concept | Where | Role | Agentic-AI analogue |
|---|---|---|---|
| `WorldGraph` | `cognition.knowledge` | Typed, queryable domain knowledge | Prompt context |

The DP continually executes a cycle consisting of the following phases:
1. `Elaboration` (via `Elaborator`): Computes value(s) based upon the current state and IO.
2. `Termination` (via `TerminationCheck`): Detects state-based ending conditions.
3. `Propose` (via `ActionFactory`): Indicates valid `Action`(s) that can be taken.
4. `Rank` (via `ActionEvaluator`, producing `ActionRank`): Uses knowledge to evaluate and score candidate actions.
5. `Apply`: Executes the single selected action, typically to modify state and/or externally actuate.

An `Operator` is a useful abstraction to associate proposal and application logic for a single action.
An `OperatorGenerator` generalizes this abstraction over a pattern of actions.


DP application typically makes state changes and can have side effects - these actions leverage neuro-symbolic reasoners...

| Concept | Where | Role | Agentic-AI analogue |
|---|---|---|---|
| `EnumClassifier`, `describe_facts`, `ModelPopulator` | `cognition.language` | Constrained LLM tasks with structured I/O | Structured outputs |
| `SearchPlanner` | `cognition.reasoning` | Optimal action sequences via search | Chain-of-thought |

To support multiple LLMs, the `cognition.language` module leverages the `PydanticAI` project.
Depending on the application, configuration may take the form of environmental variables/files (e.g., dotenv), hard-coded specification, and/or YAML.

The `SearchPlanner` implements the classic Graph Search algorithm, and so requires initial/final states, a frontier management structure, a goal test, and a succession function.
The module includes succession abstractions, much like operators, to express options that are available at each state `SearchPlannerStaticOption` (ala `Operator`) and `SearchPlannerDynamicOption` (ala `OperatorGenerator`); see see [docs/source/cook/planning.md](docs/source/cook/planning.md) / https://docs.polycog.ai/cook/planning.html).
Also, since planner state must be immutable (to support cycle detection), `cognition.knowledge.organization` includes a `WorldSnapshot` that wraps a frozen set (that is easily converted to/from a `WorldGraph`).


Greater detail: [docs/source/ideas](docs/source/ideas) / https://docs.polycog.ai/ideas

## Minimal Example

```python
from cognition import Cogent, DecisionProcess, IOContainer, Operator

# creates a cognitive agent (cogent)
# where the state of its decision process
# is represented as a boolean, initialized
# to `False` upon (re)init
my_cogent = Cogent(DecisionProcess(lambda: False))

# adds an operator named "hello"
# that can be selected when the state is False;
# if selected, it prints a message, sets the
# state to True, and terminates the
# decision process (via the `terminal` property)
@my_cogent.dp.operator("hello", terminal=True)
class HelloOperator(Operator[bool]):
    def can_perform(self, state: bool, _io: IOContainer) -> bool:
        return not state

    def perform(self, _state: bool, _io: IOContainer) -> bool:
        print("Hello, World!")
        return True

# runs the agent
my_cogent()
```

To run, make sure `cognition` has been installed in the Python environment, then execute the file.
Example (where the code was in `foo.py`)...

```
$ python foo.py 
Hello, World!
```

## Idioms & Patterns

- The DP supports either functional or imperative state, largely differentiated via the absence of a return value from actions/operator perform methods (imperative: mutate state directly; functional: return new state). Non-trivial agents typically leverage mutable state.

- An overarching goal is a largely declarative representation of task knowledge: ideally this code is readable to human and agent alike (to promote reliability), while also executable.
  - Organize files/folders to localize different forms of task knowledge (e.g., data models vs planning options vs dp operators) at each hierarchical DP level.

- `Operator` (and `OperatorGenerator`) are the preferred method of expressing control-flow knowledge.
  - As with other forms of programming, prefer smaller/simpler logic - decompose larger rules into multiple (potentially hierarchically via sub-DPs; see [docs/source/cook/hdp.md](docs/source/cook/hdp.md) / https://docs.polycog.ai/cook/hdp.html).
    - Elaboration can be used to re-use expression computation.
  - The `cognition.decision` module has multiple convenience structures that may simplify state/control representations:
    - `cognition.decision.chain` simplifies a linear sequence of steps into a single `Iterable`
    - `cognition.decision.stage` captures state machines as transitions between `Enum` values
    - `cognition.decision.state` provides optional add-ons for common state patterns

- When runtime knowledge can inform the choice of a DP action, multiple operators should be proposed and `ActionEvaluator` should dictate how to distinguish from amongst candidates; see [docs/source/cook/preference.md](docs/source/cook/preference.md) / https://docs.polycog.ai/cook/preference.html).

## Anti-Patterns

- Changing state within operator proposal (`can_perform`)

- Complex iteration/logic within operator application (`perform`)

- LLM-dictated control

- State via free-form text (i.e., LLM context)

## Where to Look

- Recipes: [docs/source/cook](docs/source/cook) / https://docs.polycog.ai/cook
- Example apps: [examples/](examples/README.md): `cli`, `choice`, `chat`, `lang`, `web-wj`
- API reference: https://docs.polycog.ai/autoapi (autogenerated)
- Tutorials: https://cognition.polycog.ai/tutorials
