# (Knowledge Augmented) Decision Process -> (KA)DP

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


## Useful DP-related Abstractions

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



## Useful DP-state-related Abstractions

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

## Typical DP Usage (e.g., isolated testing)

1. Design DP state (e.g., a custom class)
2. Instantiate a DP (with a function that supplies an initial state value)
3. Add components to the DP (e.g., operators, termination check)
4. Run (e.g., via `my_dp()`)
5. Access DP state, possibly `reinit` + re-run
