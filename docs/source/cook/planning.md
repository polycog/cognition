# Search-Based Planning

Let's use a planner to identify the fewest US coins to provide desired total cash amount.

As described in [](../ideas/planning), the search-based planner requires four inputs:
1. An initial state
   * 0 cents
2. A goal predicate
   * accumulated coins == desired total
3. A succession function
   * see below
4. A frontier factory
   * `Queue`: assuming each coin is a single action, a breadth-first search is equivalent to a plan that uses the fewest coins

```{note}
Once developed & tested, it is common to embed planning within a DP (e.g., `perform` of an `Operator`).
```

We *could* manually build a `Succession` function, but this library tries to ease this burden by structuring the problem-solving knowledge via search "options".
Below you find two complete implementations, which differ (slightly) in how the succession function is implemented.

```{note}
In practice, static options make sense when the set of available search actions are largely the same across all search states (think dense coverage), whereas dynamic options encode search-state-specific patterns to avoid considering unnecessary options (think sparse coverage).
```

## Static Option

A `SearchPlannerStaticOption` is a planning analog to an `Operator` within a DP: a single predicate-gated search action.
Once each of them has been written, the `static_opts_succession` function generates a corresponding succession function.

```{literalinclude} src/coins_static.py
:linenos:
```

## Dynamic Option

A `SearchPlannerDynamicOption` is a planning analog to an `OperatorGenerator` within a DP: a pattern for producing a set of state-specific search actions.
Once each of them has been written, the `dynamic_opts_succession` function generates a corresponding succession function.

```{literalinclude} src/coins_dynamic.py
:linenos:
```
