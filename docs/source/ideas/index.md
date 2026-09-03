# Key API Ideas

<!-- https://myst-parser.readthedocs.io/en/latest/syntax/typography.html -->

This page highlights some of the key technical aspects of the library.

:::{tip}
The tutorials provide an annotated step-by-step guide with a domain.
:::

## (Knowledge Augmented) Decision Process -> (KA)DP

![Decision Process Cycle](../_static/dp_cycle.png)

The key to orchestrating sequential decision-making -- builds upon...
* `state`: you design what (mutable) data is needed to represent progress
  * Upon initialization the DP, you provide a function to supply its initial state
* `IOContainer`: process access to non-state data/channels
  * `(i)nput`: read-only structured data (typically from external sensors)
  * `(o)utput`: channels for execution (typically a function to interact with external actuators)
  * `(e)lab`: key/computed value pairs (typically combining aspects of state + input + arguments)
  * `(a)rgs`: read-only key/value pairs to parameterize the process
* `phase`: the DP continually executes a cycle (see figure above)
  1. `Elaboration` (implemented via `Elaborator`): compute value(s) based upon state and IO
  2. `Termination` (implemented via `TerminationCheck`): detect state-based ending conditions
  3. `Propose` (implemented via `ActionFactory`): indicate valid `Action`(s)
  4. `Rank` (implemented via `ActionEvaluator`, which produces `ActionRank`): use knowledge to evaluate candidate actions
  5. `Apply` (commonly performed via operators): execute the single selected action, typically to modify state and/or externally actuate

:::{tip}
The string value (e.g., `str(my_dp)` of a DP tells you a LOT about this info).
:::

A DP can `run` individual phase/cycle(s), but commonly until a termination condition is detected.

Once a DP has terminated, it must be `reinit`ialized before future runs -- this restarts the cycle, and also sets DP state to an initial value (via the supplied function).

:::{tip}
It is not uncommon for the state initialization function to return a reference to a (mutable) object...

```python
my_state = CustomStateClass()
my_dp = DecisionProcess(lambda: my_state)
```

The effect of this pattern is that DP state persists across DP `reinit`.
:::


### Useful DP-related Abstractions

While quite flexible, the base DP (`BaseDecisionProcess`) can be cumbersome -- thus the `DecisionProcess` subclass integrates common conveniences.

* A `NamedObject` is one that has a informational read-only *name* and key/value *parameters*
* An **operator** combines proposal & application within a single context...
  * `Operator`: a 1:1 mapping from object/instance -> persistant action factory + action
    * `can_perform`: simple predicate to indicate if the object applies in the current context
    * `perform`: if selected, the action to perform
  * `OperatorGenerator`: an operator factory that dynamically generates (per cycle) only those instances that apply
    * `generate`: produce relevant operator instances (thus obviating the need for `can_perform`)
    * `perform`: if selected, the action to perform

:::{note}
Each `Operator` is a `NamedObject` (which can be useful for identification/categorization).
:::

:::{tip}
By default, a `DecisionProcess` will consider the application of an `Operator` with a `terminal` parameter to signal termination.
(This is analogous to terminal nodes within finite state machines.)
:::

* An `ActionEvaluator`'s job is to provide some number of `ActionRank` objects (which just associate a proposed action with a value, where smaller means more important)
  * The `uniform_evaluator` function provides the same value to any actions (matching an optional predicate).
  * The `sorting_evaluator` function produces rankings based upon sorting the results of applying a *key* function to each proposed action (matching an optional predicate).
    * The `operator_sorting_key` function builds a *key* function on the `<` and `==` operators.

:::{note}
The DP will not invoke any evaluator if there is only a single proposed action.
:::

:::{note}
If multiple actions share the ranking of lowest value, the DP will randomly select from amongst them.
:::



### Useful DP-state-related Abstractions

* The `SelfReinitState` class implements `__call__` in such a way that supplying an instance *as* as state initialization function allows for custom reinitialization logic.

* If DP state implements an `Elaborable` protocol, that object will get a per-cycle callback to implement within-object elaboration.
  * The `SelfElaborationState` class then makes for easy access to a within-class key-value store of elaborated values.

* The `PTEState` class provides convenient access to (p)ersistant, (t)ransient [to DP `reinit`], and (e)laborated data within a single state object.
  * And `PEState` is a special case when transient data isn't needed.

* The `create_chain_dp` function produces a DP based upon a state type that is iterable, and a supplied function that is called at each *link* in this iterable *chain*
  * The process also optionally supports the *accumulator* pattern

* The `StagedState` class provides a way to represent states in which transitions can be captured within a single `Enum` flag
  * Flow between state flag values (i.e., process `transition` knowledge) is held within the class
    * This utilizes the `EnumDispatch` class, which can `dispatch` to methods that are named the same as an enumerated value
  * Since DP operators then need only check for the current flag value, a `staged_operator` function decorates a `perform` function

### Typical DP Usage (e.g., isolated testing)

1. Design DP state (e.g., a custom class)
2. Instantiate a DP (with a function that supplies an initial state value)
3. Add components to the DP (e.g., operators, termination check)
4. Run (e.g., via `my_dp()`)
5. Access DP state, possibly `reinit` + re-run


## (Cog)nitive Ag(ent) -> Cogent

A `Cogent` provides a Perceive-Decide-Act loop by integrating...
* A supplied `DecisionProcess`
* Any number of supplied `Sensor` objects
* Any number of supplied `Actuator` objects

![Decision Process Cycle](../_static/cogent_cycle.png)

:::{note}
Each `Sensor`/`Actuator` has a name, which indicates the path within the `IOContainer` (`io.i.sensor_name` or `io.o.actuator_name`).
:::

:::{tip}
To help avoid mistakes in addressing io information, each `Sensor` can supply a *reader* to pull information from the named location within the `IOContainer` (and similarly each `Actuator` can provide an `invoker`).
:::

## Knowledge Representation & Organization

Complex agents can represent state as a `WorldGraph`, which relates a collection of `Entity` objects (i.e., nodes) via `BinaryRelation` objects (i.e., edges).
These representations are built on [Pydantic](https://pydantic.dev/docs/validation/) data models.
A `WorldGraph` instance is intended to be a single source of truth, with access mediated through the above data models.

To support read-only, hashable access to the above data, the `WorldGraph` interacts fluidly with a `WorldSnapshot` class, which wraps a frozen set of the facts that make up a class.

## Planning

The library comes with a base implementation of graph search in the `SearchPlanner` class -- this algorithm iteratively searches the space of sequential actions until it finds a goal.

Usage of the planner requires a few parameters:
* An initial planner state (`PS`)
* A predicate, which returns `True` when a goal state is supplied
* A *succession* function, which produces any planner actions (`PA`) that can be taken from the supplied planner state, as well as the associated *cost* (smaller is preferred) and resulting planner state
* A *frontier factory*, which prioritizes the search

:::{note}
The planner state is likely related to DP state, but **must** be hashable (and thus likely immutable).
:::

The library comes with common frontier factories...
* `Stack`: implements a depth-first search of the space (may be useful in memory-constrained situations)
* `Queue`: implements a breadth-first search of the space (useful to find the shortest sequence of actions to goal)
* `PriorityQueue`: implements a uniform-cost search of the space (useful to find the lowest-cost plan)
  * If supplied an *admissible* heuristic, implements A* (for lowest cost with shortest search)

To assist in developing succession functions, the library includes some useful abstractions...
* A `SearchPlannerStaticOption` represents a planner action that might be available in multiple planner states
  * The `static_opts_succession` function produces a succession function from a set of static options
* A `SearchPlannerDynamicOption` represents a class of pattern-based actions.
  * The `dynamic_opts_succession` function produces a succession function from a set of dynamic options.

:::{note}
You will notice an analog between static options and operators, as well as dynamic options and operator generators -- this comes about because DPs are also search-based.
However, while the planner is searching a space of *hypothetical* actions (and producing a discovered sequence), the DP is actually taking steps each cycle (which may involve mutating state and/or real-world actuation).
:::

## Language

The library provides multiple utilities to integrate language processing & generation within cogent decision-making.
To support access to multiple providers, and integrate with knowledge-driven data modeling, this functionality is built on [Pydantic AI](https://pydantic.dev/docs/ai/).

:::{tip}
A lot of the functionality below builds on description of data, including typing and comments -- to assist, the library includes a `DocEnum` type to provide individualized docstrings for enumerated types (and `AutoDocEnum` for automatically generated values).
:::

* Language production
  * The `describe_facts` function produces a short natural-language description of a collection of data instances.
  * The `FactDescriber` class provides re-usable functionality for instances of a single type.

* Language interpretation
  * The `EnumClassifier` class selects an enumerated value in response to a user utterance.
  * The `ModelPopulator` class attempts to provide a fully instantiated data model based in response to a user utterance.

## Guiding Principles

Flexible
: The library gives you wings to build impactful agents your way, for your problems, with your tools.

Opinionated
: Through layered modules, the API guides you towards our view of strong agent design.

Collaborative
: The library, in coordination with amazing imports, tries to play nice with Python tooling (e.g., IDE, type checking).

Declarative('ish)
: Where reasonable, the library makes encourages you to describe *what* (vs *how*).

Clean/Fun
: Where possible, abstract away boilerplate.
