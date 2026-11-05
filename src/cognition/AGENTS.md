# Using `cognition` (polycog-cognition): guide for AI coding agents

This file ships inside the `cognition` package. It is written for agents (and people) building
Python apps **with** the library. Full docs: https://docs.polycog.ai. API reference:
https://docs.polycog.ai/autoapi/. Every public symbol also has a Sphinx-style docstring, and the
package is typed (`py.typed`), so reading the source next to this file is a reliable fallback.

- Install: `pip install polycog-cognition` (Python >= 3.13). Import name: `cognition`.
- Every public name is re-exported at the top level: `from cognition import DecisionProcess, Cogent, ...`.
- The LLM features (`cognition.language`) use [Pydantic AI](https://ai.pydantic.dev) models. The
  provider extra is **not** installed by default (e.g., `pip install "pydantic-ai-slim[openai]"`).

**Contents**

- Mental model: The decision process cycle · The cogent loop
- Recipes: Operators, arguments, terminal actions · Competing actions and preferences (evaluators) · Staged workflows · Agents: sensors, actuators and the cogent loop · State that survives `reinit`, plus self-elaboration · Planning with search · Knowledge: typed facts and a world graph · Language: LLMs into and out of typed data · Putting it together: a ticket router
- Idioms: Pick a state style: functional or imperative · Keep operators small; decompose with elaboration and sub-DPs · Do expensive work once, in `perform` · Propose everything that's valid; let evaluators choose · Organize code by kind of task knowledge · Planning: options mirror operators, and snapshots make good planner states
- Anti-patterns
- Gotchas
- Debugging
- More

## Mental model

| You need to... | Use |
|---|---|
| Control flow as "match state against rules, apply one action, repeat" | `DecisionProcess` + `Operator` / `OperatorGenerator` |
| A workflow whose progress is one enum field | `StagedState` + `staged_operator` |
| Run a handler over each item of an iterable | `create_chain_dp` |
| An agent loop that reads the outside world and acts on it | `Cogent` + sensors (`create_sensor`, `@self_sensor`) + actuators (`create_actuator`, `@self_actuator`) |
| An optimal action sequence to reach a goal state | `SearchPlanner` (BFS `Queue`, DFS `Stack`, UCS `PriorityQueue`, A* `PriorityQueue(heuristic)`) |
| Typed facts and relations you can query | `Entity`, `BinaryRelation`, `WorldGraph`, `WorldSnapshot` |
| An LLM to classify, extract, or describe *into or out of typed data* | `EnumClassifier`, `ModelPopulator`, `FactDescriber` / `describe_facts` |

The design intent: deterministic Python code (decision processes, planners) owns control flow, and
LLMs are used only to translate between natural language and typed data. Keep to that split when
generating code with this library. Don't route decisions through free-form LLM output.

### The decision process cycle

A `DecisionProcess[S]` holds a state `S` and repeats five phases:

1. **Elaborate**: elaborators compute derived values into `io.e` (cleared every cycle). An
   elaborator is any function `(state, io) -> dict[str, Any]`, and each returned key becomes
   `io.e.<key>`. Add one with `dp.add_elaborator(fn)` or the `@dp.elaborator` decorator.
   `create_elaborator("name", key=lambda s, io: ..., ...)` is a handy shortcut that builds one from a
   function per key. States can also elaborate themselves (`SelfElaborationState` / `PTEState`, below).
2. **Termination check**: if any check returns `True`, or the previously applied action was
   `terminal`, the process is done.
3. **Propose**: action factories (usually operators) propose candidate actions.
4. **Rank**: if more than one candidate exists, evaluators rank them. **Smaller rank wins**, and ties
   at the top are broken **at random**.
5. **Apply**: run the chosen action. Returning `None` means "I mutated the state in place".
   Returning a value **replaces** the state.

There are two ways to end a run, and they have the same effect. Choose by what ends it. Use
`terminal=True` on an operator when *applying that action* finishes the run (e.g., "send the reply",
"report"). That way you don't restate the action's outcome as a separate check. Use a termination
check when a *condition on the state* ends the run, no matter which action led there (e.g., goal
reached, budget used up). Use one or the other for a given condition, not both.

Everything other than state is reached through the `IOContainer` passed as `io`:
`io.i.<name>` inputs (sensor data), `io.o.<name>` output channels (actuators and the built-in
`io.o.log`, a `StringIO`), `io.e.<name>` elaborated values, `io.a.<name>` run arguments. `io.i.clock.cycles`
is the current cycle count. These attributes are typed `Any`, so convert or annotate them (e.g.
`int(io.a.target)`) to keep strict type checkers happy. `io.input`, `io.output`, `io.elab` and
`io.args` give the same data as read-only mappings. Use them for optional keys and iteration
(`io.input.get("temp")`, `"temp" in io.input`, `dict(io.args)`), because attribute access raises
`AttributeError` when a key is missing.

### The cogent loop

A `Cogent` wraps one root decision process. Each call, `agent(repeat_p, max_cycles, dp_err_p,
other_err_p, **args)`, runs this loop:

1. `dp.reinit()`, and add `**args` as `io.a.*`. They stay available for the whole call and are
   removed when it returns.
2. Repeat:
   1. **Perceive**: read every sensor once into `io.i.<name>`.
   2. **Decide and act**: run the DP until it terminates, or for at most `max_cycles` cycles (even if
      it hasn't finished). Actuators fire from inside its actions.
   3. **Gate**: ask `repeat_p(cogent)` whether to continue. The default, `Cogent.gate_run_once`,
      stops, and `Cogent.gate_run_forever` never does. If perceiving or the DP run raised an error, `dp_err_p(msg, cogent)`
      (for `DecisionProcessExecutionError`) or `other_err_p(exc, cogent)` decides instead. Without
      the matching predicate, the error propagates.
   4. If continuing, `dp.reinit()` and go back to step 2.1.

So ending the DP run (with a `terminal` operator or a termination check) is how a DP hands control
back to the loop, for example to perceive new input. Because the DP is reinitialized between
iterations, anything that must carry over belongs in a `SelfReinitState` instance (see "State that
survives `reinit`" below), as in the `cli` example app, or on the cogent object itself.

## Recipes

### Operators, arguments, terminal actions

```python
from cognition import DecisionProcess, IOContainer, Operator

type Count = dict[str, int]

dp = DecisionProcess[Count](lambda: {"n": 0})


@dp.operator("increment", step=2)  # instantiates Increment("increment", step=2) and adds it
class Increment(Operator[Count]):
    def can_perform(self, state: Count, io: IOContainer) -> bool:
        return state["n"] < int(io.a.target)  # io.a.* = keyword args passed to dp(...)

    def perform(self, state: Count, io: IOContainer) -> None:
        state["n"] += self.params["step"]  # mutate in place -> return None


@dp.operator("report", terminal=True)  # any `terminal` param ends the run after it is applied
class Report(Operator[Count]):
    def can_perform(self, state: Count, io: IOContainer) -> bool:
        return state["n"] >= int(io.a.target)

    def perform(self, state: Count, io: IOContainer) -> None:
        io.o.log.write(f"reached {state['n']}")


final = dp(target=5)  # final state if it finished cleanly, otherwise None
assert final == {"n": 6}
assert dp.log == "reached 6"

dp.reinit()  # required before running again: a finished DP stays finished
assert dp(target=1) == {"n": 2}
```

### Competing actions and preferences (evaluators)

With two or more proposals per cycle you **must** add at least one evaluator. Without one, the run
raises `DecisionProcessExecutionError(NO_RANK)`.

```python
from typing import cast

from cognition import DecisionProcess, IOContainer, NamedObject, Operator, sorting_evaluator


class Add(Operator[list[int]]):
    def can_perform(self, state: list[int], io: IOContainer) -> bool:
        return state[0] + int(self.params["step"]) <= int(io.a.target)

    def perform(self, state: list[int], io: IOContainer) -> None:
        state[0] += self.params["step"]


dp = DecisionProcess[list[int]](lambda: [0])
for step in (1, 5):
    dp.add_operator(Add("add", step=step))
dp.add_termination_check(lambda s, io: s[0] == io.a.target)

# prefer bigger steps (smaller key -> smaller rank -> preferred)
dp.add_action_evaluator(
    sorting_evaluator(lambda a, s, io: -cast(NamedObject, a).params["step"], name="big_first")
)

assert dp(target=7) == [7]  # 5, then 1, then 1
```

Other ranking helpers: `uniform_evaluator(Rank.HIGH, predicate)` (`Rank.HIGH < MEDIUM < LOW`),
`operator_sorting_key()` (sorts by comparing the operator objects themselves). For per-cycle
dynamic proposals, subclass `OperatorGenerator` (classmethods `get_name` and `generate`) and add it
with `dp.add_generator(GenType, extra)` or `@dp.generator(extra)`.

### Staged workflows

```python
from dataclasses import dataclass

from cognition import AutoDocEnum, DecisionProcess, IOContainer, StagedState, staged_operator


class Step(AutoDocEnum):
    """Signup flow"""

    ASK = "ask for a username"
    CONFIRM = "check the username"
    DONE = "finished"


@dataclass
class Signup(StagedState[Step]):
    stage: Step = Step.ASK
    username: str = ""

    # one method per non-terminal stage, named stage.name.lower(); it returns the next stage
    def ask(self, username: str) -> Step:
        self.username = username
        return Step.CONFIRM

    def confirm(self, ok: bool) -> Step:
        return Step.DONE if ok else Step.ASK


dp = DecisionProcess(Signup)  # Signup() builds a fresh state on every reinit


@staged_operator(dp, Step.ASK)
def _ask(s: Signup, io: IOContainer) -> dict[str, str]:
    return {"username": io.i.typed}  # returned dict -> kwargs of Signup.ask


@staged_operator(dp, Step.CONFIRM)
def _confirm(s: Signup, io: IOContainer) -> dict[str, bool]:
    return {"ok": s.username.isidentifier()}


dp.add_termination_check(lambda s, io: s.stage is Step.DONE)  # no operator handles DONE

dp.set_input_data("typed", "ada")
assert dp() == Signup(stage=Step.DONE, username="ada")
```

### Agents: sensors, actuators and the cogent loop

A `Cogent` wraps one root decision process, plus the sensors and actuators it reads and drives.
See "The cogent loop" above for what each call does.

```python
from cognition import Cogent, DecisionProcess, IOContainer, Operator, create_actuator, create_sensor

readings = iter([3, 12])
temp = create_sensor("temp", lambda: next(readings))  # -> io.i.temp
alerts: list[str] = []
alarm = create_actuator("alarm", alerts.append)  # -> io.o.alarm(param)

dp = DecisionProcess[None](lambda: None)


@dp.operator("check", terminal=True)
class Check(Operator[None]):
    def can_perform(self, state: None, io: IOContainer) -> bool:
        return True

    def perform(self, state: None, io: IOContainer) -> None:
        if temp.read(io) > io.a.limit:  # typed alternative to io.i.temp
            alarm.invoke(io, f"too hot: {temp.read(io)}")  # typed alternative to io.o.alarm(...)


agent = Cogent(dp, name="thermostat").add_sensor(temp).add_actuator(alarm)
agent(limit=10)  # reads 3
agent(limit=10)  # reads 12
assert alerts == ["too hot: 12"]
```

Subclass style, where methods become sensors and actuators named after the method:

```python
from typing import Any

from cognition import Cogent, DecisionProcess, IOContainer, Operator, self_actuator, self_sensor


class EchoBot(Cogent[DecisionProcess[None]]):
    def __init__(self, inbox: list[str], **kwargs: Any) -> None:
        self.inbox, self.outbox = inbox, list[str]()
        super().__init__(DecisionProcess(lambda: None), name="echo", **kwargs)

    @self_sensor
    def message(self) -> str:  # -> io.i.message
        return self.inbox.pop(0)

    @self_actuator
    def reply(self, text: str) -> None:  # -> io.o.reply(text)
        self.outbox.append(text)


bot = EchoBot(["hi", "bye"])


@bot.dp.operator("echo", terminal=True)
class Echo(Operator[None]):
    def can_perform(self, state: None, io: IOContainer) -> bool:
        return True

    def perform(self, state: None, io: IOContainer) -> None:
        io.o.reply(io.i.message.upper())


bot(repeat_p=lambda c: bool(bot.inbox))  # loop while there is input
assert bot.outbox == ["HI", "BYE"]
```

### State that survives `reinit`, plus self-elaboration

`reinit()` calls the state initializer again (and `Cogent` reinits on every call). To keep state
across runs, pass an instance of a `SelfReinitState` subclass as the initializer: it returns
itself on reinit. `PTEState[P, T]` bundles **P**ersistent state (`.p`), **T**ransient state (`.t`,
rebuilt on each reinit) and **E**laborated values (`.e`, recomputed every cycle by your
`_elaborate`). `PEState[P]` is the version with no transient part.

```python
from collections.abc import Mapping
from typing import Any

from cognition import DecisionProcess, IOContainer, PTEState


class Tally(PTEState[list[str], list[str]]):  # p: all-time history, t: this run only
    def _elaborate(self, io: IOContainer) -> Mapping[str, Any]:
        return {"full": len(self.t) >= io.a.batch}


def record(s: Tally, io: IOContainer) -> None:  # a bare action: (state, io) -> state | None
    s.p.append("x")
    s.t.append("x")


state = Tally([], list)
dp = DecisionProcess(state)  # pass the instance itself, NOT `lambda: state`
dp.add_action_factory(lambda s, io: record)  # factories return one action or an iterable
dp.add_termination_check(lambda s, io: s.e.full)

dp(batch=2)
dp.reinit()
dp(batch=3)
assert (len(state.p), len(state.t)) == (5, 3)
```

### Planning with search

```python
from cognition import PriorityQueue, SearchPlanner, SearchPlannerStaticOption, static_opts_succession


class Move(SearchPlannerStaticOption[tuple[int, int], str]):
    def __init__(self, name: str, dx: int, dy: int) -> None:
        super().__init__(name)  # the action reported in the plan
        self.dx, self.dy = dx, dy

    def is_available(self, s: tuple[int, int]) -> bool:
        return 0 <= s[0] + self.dx <= 4 and 0 <= s[1] + self.dy <= 4

    def then(self, s: tuple[int, int]) -> tuple[tuple[int, int], int]:
        return (s[0] + self.dx, s[1] + self.dy), 1  # (next state, step cost)


goal = (3, 2)
planner = SearchPlanner(
    (0, 0),  # states must be hashable
    lambda s: s == goal,
    static_opts_succession(Move("R", 1, 0), Move("L", -1, 0), Move("U", 0, 1), Move("D", 0, -1)),
    lambda: PriorityQueue(lambda s: abs(goal[0] - s[0]) + abs(goal[1] - s[1])),  # A*
).run()  # .run(max_steps=N) searches incrementally; check .still_searching

assert planner.plan_found and planner.plan_cost == 5 and len(planner.plan) == 5
```

`successors` can also be any function `state -> Iterable[(next_state, action, cost)]`, or
`dynamic_opts_succession(*OptionTypes)` where each `SearchPlannerDynamicOption` subclass has a
classmethod `when(state)` that yields the instances that apply. `planner.plan` and `plan_cost`
raise `RuntimeError` if no plan was found.

### Knowledge: typed facts and a world graph

```python
from pydantic import Field

from cognition import BinaryRelation, Entity, WorldGraph, WorldSnapshot


class Block(Entity):
    """A toy block"""

    color: str = Field(description="block color")  # descriptions feed the LLM prompts


class On(BinaryRelation):
    """entity1 sits directly on entity2"""

    entity1: Block = Field(frozen=True)  # narrowing entity1/entity2 requires frozen=True
    entity2: Block = Field(frozen=True)


wg = WorldGraph()
a = wg.add_entity(Block(name="A", color="red")).e  # node id = entity name
b = wg.add_entity(Block(name="B", color="blue")).e
wg.add_relation(On(entity1=a, entity2=b))  # both ends must already be in the graph

snap: WorldSnapshot = wg.snapshot  # immutable, hashable copy of every fact
assert snap.entity_by_name("A") == a.freeze()
assert len(list(snap.filter_relations(On, e2=b.freeze()))) == 1
assert len(list(snap.by(Block, lambda blk: blk.color == "red"))) == 1

wg.add_entity(a.replace(color="green"))  # replace() copies with custom-field changes; re-adding by name updates the node
assert wg.get_entity("A").e.color == "green"  # linked=False returns a plain Entity (cast to use fields)
assert WorldGraph.from_snapshot(snap).snapshot == snap  # round-trip
```

`freeze()` returns a hashable `Frozen<Type>` copy (lists become tuples, sets become frozensets) that
`isinstance`-matches the original class, and `thaw()` gives back a mutable copy. Snapshots
hold frozen facts. One edge exists per `(entity1, entity2, relation class name)`.

### Language: LLMs into and out of typed data

Every call takes a Pydantic AI `Model` instance as `llm` and is **synchronous** (`run_sync`). From
async code, see the event-loop gotcha below.
Docstrings, `Field(description=...)` and `DocEnum` / `AutoDocEnum` member docs are written into
the prompts automatically, so document your types well. `DocEnum` members take an explicit value
and an optional docstring (`BOOK = "book", "reserve a table"`). `AutoDocEnum` members are numbered
automatically (1, 2, ...), and the string you write *is* the docstring (`ASK = "ask for a username"`).
`EnumClassifier` shows the model each member's value and docstring, but not its name, so with
`AutoDocEnum` the docstrings carry all the meaning.

```python
from pydantic import BaseModel, Field
from pydantic_ai.models.test import TestModel  # offline stand-in; use a real model in apps

from cognition import DocEnum, EnumClassifier, ModelPopulator, describe_facts


class Intent(DocEnum):
    """What the user wants"""

    BOOK = "book", "reserve a table"
    CANCEL = "cancel", "cancel an existing reservation"


class Booking(BaseModel):
    """A restaurant booking"""

    party_size: int = Field(description="number of guests")
    time: str = Field(description="requested time, HH:MM 24h")


llm = TestModel()  # in apps: e.g. OpenAIResponsesModel(...) or AnthropicModel(...) from pydantic_ai.models.*

intent, conf = EnumClassifier(Intent, "restaurant assistant")("table for 4 at 7pm", llm, num_trials=3)
# intent: Intent | None (None = nothing fits OR every trial failed); float(conf) = agreement across trials

booking = ModelPopulator(Booking, "restaurant assistant")("table for 4 at 7pm", llm)
assert isinstance(booking, Booking)  # raises if the model cannot produce a valid instance

prompt = describe_facts([booking], "restaurant assistant", llm, debug=True)  # debug=True: prompt only
assert "party_size" in prompt

# in tests, choose the reply with custom_output_args, using the helper's output schema
cancel = TestModel(custom_output_args={"value": "cancel"})  # {"value": None} -> no match
assert EnumClassifier(Intent, None)("cancel it", cancel)[0] is Intent.CANCEL
two_at_six = TestModel(custom_output_args={"party_size": 2, "time": "18:30"})
assert ModelPopulator(Booking, None)("2 at 6:30pm", two_at_six).party_size == 2
```

`EnumClassifier` swallows per-trial errors (they count as `None` votes). `ModelPopulator`,
`FactDescriber` and `describe_facts` let errors propagate. Each class has a `.prompt(...)` method for
inspecting the exact prompt without calling a model.

**Testing without a real model:** pass a Pydantic AI test model as `llm`. See their
[testing guide](https://pydantic.dev/docs/ai/guides/testing/) for how `TestModel` and `FunctionModel`
work. With a plain `TestModel()`, `EnumClassifier` always gets the first enum member. To choose
the reply, set `custom_output_args` using the helper's output schema, as shown above:
`{"value": <member value>}` (or `{"value": None}`) for `EnumClassifier`, and your model's fields
for `ModelPopulator`. For replies that depend on the input, use `FunctionModel`. The utterance is
embedded in the helper's prompt (see `.prompt(...)`).

### Putting it together: a ticket router

A cogent reads one ticket per loop iteration. It classifies the ticket once (in `perform`, with
the result stored in typed state), then routes it. Outages may go to on-call *or* the general
queue, and an evaluator decides between them.

```python
import json
from dataclasses import dataclass
from typing import cast

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from cognition import (
    Cogent, DecisionProcess, DocEnum, EnumClassifier, IOContainer, NamedObject, Operator,
    create_actuator, create_sensor, sorting_evaluator,
)


class Category(DocEnum):
    """Kind of support ticket"""

    OUTAGE = "outage", "a service is down or failing"
    BILLING = "billing", "charges, invoices or refunds"


def keyword_llm(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """Offline stand-in; in an app, use a real model (e.g. OpenAIResponsesModel(...))"""
    part = messages[-1].parts[-1]
    assert isinstance(part, UserPromptPart) and isinstance(part.content, str)
    utterance = part.content.split("== Utterance ==")[1].split("Please choose")[0].lower()
    value = "outage" if "down" in utterance else "billing" if "charge" in utterance else None
    return ModelResponse(parts=[TextPart(json.dumps({"value": value}))])  # the classifier's reply shape


@dataclass
class Ticket:
    category: Category | None = None
    classified: bool = False


classifier = EnumClassifier(Category, "support desk triage")
llm = FunctionModel(keyword_llm)
dp = DecisionProcess(Ticket)  # a fresh Ticket on every loop iteration (reinit)


@dp.operator("classify")
class Classify(Operator[Ticket]):
    def can_perform(self, state: Ticket, io: IOContainer) -> bool:
        return not state.classified

    def perform(self, state: Ticket, io: IOContainer) -> None:  # the LLM call: once, here
        state.category, _confidence = classifier(io.i.ticket, llm)
        state.classified = True


class Route(Operator[Ticket]):
    def can_perform(self, state: Ticket, io: IOContainer) -> bool:  # allowed, not "best"
        return state.classified and self.params["only"] in (None, state.category)

    def perform(self, state: Ticket, io: IOContainer) -> None:
        io.o.send((io.i.ticket, self.params["queue"]))


dp.add_operator(Route("route", queue="oncall", only=Category.OUTAGE, terminal=True))
dp.add_operator(Route("route", queue="general", only=None, terminal=True))
priority = {"oncall": 0, "general": 1}  # every queue is ranked; unranked actions are never chosen
dp.add_action_evaluator(
    sorting_evaluator(lambda a, s, io: priority[cast(NamedObject, a).params["queue"]], name="priority")
)

inbox = ["the site is down", "double charge on my invoice", "love the app"]
sent: list[tuple[str, str]] = []
agent = Cogent(dp, name="router")
agent.add_sensor(create_sensor("ticket", lambda: inbox.pop(0)))
agent.add_actuator(create_actuator("send", sent.append))
agent(repeat_p=lambda c: bool(inbox))

assert sent == [
    ("the site is down", "oncall"),
    ("double charge on my invoice", "general"),
    ("love the app", "general"),
]
```

## Idioms

### Pick a state style: functional or imperative

The return value of an action decides the style. **Functional** actions return the next state,
which replaces the current one. This suits small, immutable states (a `bool`, an `int`, a frozen
dataclass). **Imperative** actions mutate the state in place and return `None`. Non-trivial agents
usually use a mutable state object (a dataclass, `StagedState`, `PTEState`) with imperative actions,
as in most recipes above.

```python
from cognition import DecisionProcess, IOContainer


def step(s: int, io: IOContainer) -> int:  # functional: returns the next state
    return s + 1


dp = DecisionProcess[int](lambda: 0)
dp.add_action_factory(lambda s, io: step)
dp.add_termination_check(lambda s, io: s >= 3)
assert dp() == 3
```

### Keep operators small; decompose with elaboration and sub-DPs

- **One operator, one rule:** keep `can_perform` to a short condition and `perform` to a short step.
  Split larger rules into several operators that take effect over successive cycles.
- **Compute shared conditions once per cycle** with an elaborator. Several operators and
  termination checks can then read the result from `io.e`, so the logic isn't duplicated and can't drift apart.
- **Move a self-contained sub-problem into its own DP** and call it from a parent operator's
  `perform`, through a small wrapper that reinitializes it, passes `io.a` arguments, and extracts
  the result. You can then test the sub-DP on its own. See the
  [Hierarchical Decision Processes](https://docs.polycog.ai/cook/hdp.html) recipe.

```python
from dataclasses import dataclass, field

from cognition import DecisionProcess, IOContainer, Operator, create_elaborator


# --- sub-DP: digital root (repeatedly sum the digits until one digit remains) ---
@dataclass
class RootState:
    value: int = 0
    started: bool = False


dp_root = DecisionProcess(RootState)
dp_root.add_elaborator(  # computed once per cycle, read by an operator and the termination check
    create_elaborator("root_elab", single_digit=lambda s, io: s.started and s.value < 10)
)
dp_root.add_termination_check(lambda s, io: bool(io.e.single_digit))


@dp_root.operator("start")
class Start(Operator[RootState]):
    def can_perform(self, state: RootState, io: IOContainer) -> bool:
        return not state.started

    def perform(self, state: RootState, io: IOContainer) -> None:
        state.value, state.started = int(io.a.n), True


@dp_root.operator("sum_digits")
class SumDigits(Operator[RootState]):
    def can_perform(self, state: RootState, io: IOContainer) -> bool:
        return state.started and not io.e.single_digit

    def perform(self, state: RootState, io: IOContainer) -> None:
        state.value = sum(int(d) for d in str(state.value))


def digital_root(n: int) -> int:
    """Wrapper: reinit the sub-DP, pass arguments, extract the result"""
    dp_root.reinit()
    result = dp_root(suppress_errors=False, n=n)
    assert result is not None
    return result.value


assert digital_root(9875) == 2  # the sub-DP is testable on its own: 9875 -> 29 -> 11 -> 2


# --- parent DP: calls the sub-DP from an operator's perform ---
@dataclass
class BatchState:
    todo: list[int] = field(default_factory=list)
    roots: dict[int, int] = field(default_factory=dict)


dp_batch = DecisionProcess(lambda: BatchState(todo=[38, 9875, 7]))
dp_batch.add_termination_check(lambda s, io: not s.todo)


@dp_batch.operator("next")
class Next(Operator[BatchState]):
    def can_perform(self, state: BatchState, io: IOContainer) -> bool:
        return bool(state.todo)

    def perform(self, state: BatchState, io: IOContainer) -> None:
        n = state.todo.pop(0)
        state.roots[n] = digital_root(n)


final = dp_batch()
assert final is not None and final.roots == {38: 2, 9875: 2, 7: 7}
```

### Do expensive work once, in `perform`

Elaborators, termination checks, `can_perform` and evaluators run every cycle (`can_perform` for
every operator), so keep them cheap and read-only. Expensive work (LLM calls, planner searches,
network or database I/O) belongs in an operator's `perform`, which runs only when that action is
chosen. Store the result in state so later rules can read it (e.g., `state.intent`, `state.plan`),
as `MakePlan` does in the planning idiom below. Work triggered by new input can also happen before
the DP runs: in a sensor (read once per cogent loop iteration), or before calling the cogent, with
the result passed as a run argument, as the `chat` example app does with intent classification.
LLMs add a second reason: a classifier called in `can_perform` could answer differently each
cycle, so the set of proposals would change at random.

### Propose everything that's valid; let evaluators choose

`can_perform` should answer "is this action *allowed* right now?", not "is it the *best* action?".
When runtime knowledge (preferences, costs, policies) should decide between valid actions, propose
all of them and rank them with evaluators. Don't fold the preference into mutually exclusive
`can_perform` conditions. Keeping the two apart means:

- each operator's applicability stays independent and easy to check;
- preference knowledge lives in one place, where it can be swapped, layered, or tested on its own;
- when the preferred action stops being valid, the next-best one is still proposed.

How several evaluators combine: their rankings are pooled and the smallest rank wins, so an
action's best rank from any evaluator counts. An action that **no** evaluator ranks is never chosen
when there are competing proposals. See "Competing actions and preferences" above and the
[Decision Preferences](https://docs.polycog.ai/cook/preference.html) recipe. When the task itself makes
actions mutually exclusive (e.g., one operator per stage), no evaluator is needed.

### Organize code by kind of task knowledge

Aim for task knowledge that reads declaratively: people and agents can review it, and it stays
executable. Split files by the *kind* of knowledge, and repeat the split at each level of a DP
hierarchy. Language and planning knowledge is usually local to the DP that uses it (e.g., the root
DP classifies intents, and a sub-DP runs its own planner), so keep it in that DP's folder. Only truly
shared pieces live at the top. One possible starting layout:

```text
my_agent/
├── main.py              # build the Cogent (root DP, sensors, actuators) and run it
├── env.py               # sensors and actuators: the I/O boundary
├── domain.py            # shared typed data: Entity / BinaryRelation subclasses, enums, pydantic models
├── llm.py               # shared model setup (provider, model name, settings)
└── dp/                  # root DP
    ├── state.py
    ├── operators.py     # operators / generators
    ├── evaluators.py    # preferences
    ├── language.py      # e.g., the intent EnumClassifier used by root operators
    └── validate/        # a sub-DP: same split, plus its wrapper function
        ├── __init__.py  # wrapper, e.g. validate(...) -> result
        ├── state.py
        ├── operators.py
        └── planning.py  # e.g., a local SearchPlanner called from an operator's perform
```

There are two ways to attach knowledge to a DP:

- **Decorators** (`@dp.operator`, `@staged_operator`, `@dp.termination_check`) register when their
  module is imported, so they must live next to the `dp` object or in a module that is reliably
  imported. This suits one file per DP, as in the `cli` example app.
- **Assembly** suits larger apps: define operators, generators and evaluators as plain classes and
  factory functions, and wire them up in one place (`dp.add_operator(...)`, `dp.add_generator_c(...)`,
  `dp.add_action_evaluator(...)`), as in the `choice` example app. The knowledge modules then have no
  import side effects, and you can build variants (e.g., a different evaluator) or test setups from
  the same pieces.

### Planning: options mirror operators, and snapshots make good planner states

- **Options are the planner's operators.** `SearchPlannerStaticOption` works like `Operator`: one
  fixed transition, gated by `is_available`. `SearchPlannerDynamicOption` works like
  `OperatorGenerator`: its classmethod `when(state)` yields the transitions that apply.
- **Planner states must be immutable and hashable**, because the search keeps an explored set to
  detect cycles. `then()` must return a *new* state and never mutate its input. For knowledge-rich
  states, use a `WorldSnapshot`: take one from a `WorldGraph` (`wg.snapshot`), derive successors with
  `snap.copy(add=..., remove=...)`, and go back to an editable graph with `WorldGraph.from_snapshot`.
- **Call the planner from a DP operator's `perform`**, and store the plan in DP state for later
  operators to carry out. To stay responsive on large problems, call `planner.run(max_steps=N)` once
  per cycle from an operator that keeps being proposed while `planner.still_searching`.

```python
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Self

from pydantic import Field

from cognition import (
    BinaryRelation,
    DecisionProcess,
    Entity,
    IOContainer,
    Operator,
    PriorityQueue,
    SearchPlanner,
    SearchPlannerDynamicOption,
    WorldGraph,
    WorldSnapshot,
    dynamic_opts_succession,
)


class Block(Entity):
    """A movable block"""


class Table(Entity):
    """The table: always has room"""


class On(BinaryRelation):
    """entity1 rests directly on entity2"""

    entity1: Block = Field(frozen=True)
    entity2: Block | Table = Field(frozen=True)


class MoveOnto(SearchPlannerDynamicOption[WorldSnapshot, str]):
    """Move a clear block onto a clear block or the table"""

    def __init__(self, rel: On, target: Block | Table) -> None:
        super().__init__(f"move {rel.entity1.name} onto {target.name}")  # the plan's action
        self.rel, self.target = rel, target

    @classmethod
    def when(cls, state: WorldSnapshot) -> Iterator[Self]:  # like OperatorGenerator.generate
        rels = list(state.by(On))
        covered = {r.entity2.name for r in rels}
        targets = [b for b in state.by(Block) if b.name not in covered] + list(state.by(Table))
        for rel in rels:
            if rel.entity1.name not in covered:  # only clear blocks can move
                for target in targets:
                    if target.name not in (rel.entity1.name, rel.entity2.name):
                        yield cls(rel, target)

    def then(self, state: WorldSnapshot) -> tuple[WorldSnapshot, int]:  # new state, never mutate
        moved = On(entity1=self.rel.entity1, entity2=self.target)
        return state.copy(add=[moved], remove=[self.rel]), 1


# start: C on A; A and B on the table. goal: A on B on C (the "Sussman anomaly")
wg = WorldGraph()
a, b, c = (wg.add_entity(Block(name=n)).e for n in "ABC")
table = wg.add_entity(Table(name="table")).e
for rel in (On(entity1=c, entity2=a), On(entity1=a, entity2=table), On(entity1=b, entity2=table)):
    wg.add_relation(rel)
goal = [On(entity1=a, entity2=b), On(entity1=b, entity2=c)]


def unmet(s: WorldSnapshot) -> int:  # A* heuristic: each move fixes at most one goal relation
    return sum(g not in s for g in goal)


@dataclass
class Robot:
    world: WorldGraph
    plan: list[str] = field(default_factory=list)
    planned: bool = False


dp = DecisionProcess(lambda: Robot(wg))
dp.add_termination_check(lambda s, io: s.planned)


@dp.operator("plan")
class MakePlan(Operator[Robot]):
    def can_perform(self, state: Robot, io: IOContainer) -> bool:
        return not state.planned

    def perform(self, state: Robot, io: IOContainer) -> None:
        planner = SearchPlanner(
            state.world.snapshot,  # immutable, hashable copy of the graph
            lambda s: unmet(s) == 0,
            dynamic_opts_succession(MoveOnto),
            lambda: PriorityQueue(unmet),
        ).run()
        state.plan = list(planner.plan) if planner.plan_found else []
        state.planned = True


final = dp()
assert final is not None
assert final.plan == ["move C onto table", "move B onto C", "move A onto B"]
```

## Anti-patterns

- **Changing state (or causing side effects) in `can_perform`.** Every operator's `can_perform` runs
  in every propose phase, including for actions that are never chosen. Changes made there happen
  regardless of the decision, and they break the guarantee that only the applied action changes the
  state. The same goes for elaborators, termination checks and evaluators: they should only
  *read*. **Instead:** make changes in `perform`, and compute derived values in elaborators. (For
  expensive calls, see "Do expensive work once, in `perform`".)
- **Complex iteration or logic inside `perform`.** A loop inside one action hides its intermediate
  steps from the DP: no termination checks or re-ranking between them, nothing visible in
  `print(dp)` or the logs, no limit from `max_cycles`, and it's harder to test. **Instead:** do one
  step per cycle with small operators, use `create_chain_dp` for a sequence, a sub-DP for a
  self-contained sub-problem, or `SearchPlanner` for a search.
- **Letting an LLM dictate control flow**, e.g., asking a model which operator to run, or letting it
  call tools directly. This makes the agent's behavior non-deterministic and impossible to verify.
  **Instead:** have the language helpers turn text into a typed value (`EnumClassifier` → an enum
  member, `ModelPopulator` → a model instance), check it (handle `None`, check `float(confidence)`),
  put it in state or `io.a`, and let operators and evaluators decide.
- **Keeping state as free-form text**, such as an accumulated conversation transcript that operators
  re-parse, or LLM context as the source of truth. **Instead:** keep typed state (dataclasses,
  pydantic models) or a `WorldGraph`, and generate text from it only when needed for output
  (`describe_facts`, `FactDescriber`).

## Gotchas

- **A finished DP stays finished.** Calling `dp()` again returns the old state immediately. Call
  `dp.reinit()` first. (`Cogent.__call__` reinits for you.)
- **`dp()` hides errors by default**: it returns `None` both on an exception *and* when
  `max_cycles` ran out before termination. Use `dp(suppress_errors=False)` (raises `RuntimeError`
  chained to the cause) or call `dp.run_until_done()` directly while developing.
- **No proposals while not done** raises `DecisionProcessExecutionError(NO_PROPOSAL)`. Every reachable
  non-terminal state needs an applicable operator, or a termination check that fires first.
- **`run_until_done()` has no cycle limit.** Pass `max_cycles` when termination isn't guaranteed.
- **Return value of an action:** `None` means mutate in place. Any other value replaces the state, so a
  stray `return True` from `perform` silently swaps your state for `True`.
- **Ties at the best rank are chosen at random.** Make ranks distinct (or seed `random`) if you need
  reproducible runs.
- **Termination is checked after elaboration and before proposing.** A `terminal` action ends the run
  at the *next* termination check, so the action itself always completes.
- **`num_cycles` counts termination checks**, so 3 applied actions followed by termination shows 4.
- **`io.e` is cleared each cycle**, and `io.a` values exist only during the `dp(...)` / `cogent(...)`
  call that supplied them. Persist anything long-lived in the state.
- **Sensors are read once per cogent loop iteration**, not once per DP cycle.
- **An `Elaborable` state is detected once, at `DecisionProcess` construction**, using the first state
  instance. Use `DecisionProcess(state_instance)` with `SelfElaborationState` / `PTEState`, not a
  factory that builds new objects.
- **`create_chain_dp` stops at the first `None` item**, because `None` marks exhaustion. It
  re-iterates the original iterable on `reinit`, so pass a list rather than a one-shot generator.
- **Typing:** `Action` is a plain callable type, so cast to `NamedObject` to read `.name` / `.params`.
  In evaluator predicates, match on `.name` rather than `str(action)`, because `str()` includes the
  params (e.g., `add[step=5]`), except underscore-prefixed ones such as the auto-added `_op`
  operator self-reference.
- **`BinaryRelation` subclasses must re-declare `entity1` / `entity2` with `Field(frozen=True)`**,
  or class creation raises `TypeError`. The same applies to any field named in `fixed_field_names()`.
- **The language helpers are blocking, and they fail inside a running event loop.** From `async`
  code (FastAPI handlers, bots, `asyncio.run(...)` apps), call them through
  `await asyncio.to_thread(helper, ...)`, e.g.
  `intent, conf = await asyncio.to_thread(classifier, utterance, llm)`. Called directly,
  `ModelPopulator`, `FactDescriber` and `describe_facts` raise `RuntimeError`, and `EnumClassifier`
  silently returns `None`, because it counts errors as `None` votes. Its confidence then still
  looks high, since confidence only measures agreement across trials.

## Debugging

- `print(dp)` shows phase, state, the chosen action, proposals, rankings and all registered components.
  Wrap your own lambdas with `stringify("name")(fn)`, or pass `name=` to evaluator helpers, so they
  print readably.
- Step manually with `dp.run_phase()`, `dp.run_cycles(n)`, or iterate `for _ in dp.cycles(): ...` /
  `dp.phases()`. Check `dp.chosen_action`, `dp.done`, `dp.num_cycles` and `dp.io`.
- Logging: the library logs to the `cognition` logger (a `NullHandler` by default). Enable it with
  `logging.basicConfig(); logging.getLogger("cognition").setLevel(logging.INFO)`. `DEBUG` is very verbose.
- Importing `cognition` sets `PYDANTIC_AI_NO_BANNER=1` unless it is already set.

## More

- Concepts: https://docs.polycog.ai/ideas/
- Cookbook: https://docs.polycog.ai/cook/
- Example apps: https://github.com/polycog/cognition/tree/main/examples
- Tutorials: https://github.com/polycog/tutorials
- Pydantic AI (models, providers, testing): https://pydantic.dev/docs/ai/llms.txt
