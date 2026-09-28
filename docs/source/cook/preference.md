# Decision Preferences

As described in [](../ideas/kadp.md), the `Rank` phase provides knowledge to select from amongst multiple proposed actions.
In the code below, three "Choice" operators (`a`, `b`, and `c`) are proposed in a single-decision DP - the `Cogent` is run multiple items to illustrate the result of utilizing different preference-knowledge approaches:

```{literalinclude} src/eval.py
:linenos:
```

## Ranking Semantics

* Any comparable value can be utilized for rank values
  * Smaller values are considered more desirable
  * For convenience, the `Rank` enumeration is included for simple cases: LOW/MEDIUM/HIGH (where LOW has the largest value).
* Multiple evaluators can be utilized - the decision is made based upon the union of `ActionRank` objects produced.

## Uniform -> Random

```{literalinclude} src/eval.py
:start-after: START all_same
:end-before: END all_same
```

The `uniform_evaluator` function produces an evaluator that provides the supplied rank value to *ALL* proposed actions.

Thus, using this strategy produces a mix of a/b/c results.

## Uniform + Predicate -> Categories

```{literalinclude} src/eval.py
:start-after: START op_classes
:end-before: END op_classes
```

The `uniform_evaluator` function optionally accepts a predicate to filter those actions to which an instance supplies ranking information.

In this case there are two categories: "a" (`LOW` rank) and all others (`HIGH` rank), and thus this strategy produces a mix of b/c results.

## Sorting: Absolute Values -> Relative Ranks

```{literalinclude} src/eval.py
:start-after: START op_sorting_abs
:end-before: END op_sorting_abs
```

The `sorting_evaluator` function produces an evaluator that sorts the proposed actions (using a required `sorting_key` function) and then automatically produces appropriate ranks based upon the relative ordering.

In this case, the sorting key is based upon a hard-coded dictionary associating action -> value; this strategy thus always produces "c" as the final result (since it will be deterministically sorted first amongst the options).

```{note}
Given this structure, cogents can adaptively modify decision-selection knowledge based upon feedback (e.g., via [TD Learning](https://en.wikipedia.org/wiki/Temporal_difference_learning)).
```

## Sorting: Object Comparison -> Relative Ranks

A useful companion to the `sorting_evaluator` function is `operator_sorting_key`:

```{literalinclude} src/eval.py
:start-after: START op_sorting_rel
:end-before: END op_sorting_rel
```

This combination will expect that objects can be pairwise compared (via `__eq__` and `__lt__`):

```{literalinclude} src/eval.py
:start-after: START op_sorting_defn
:end-before: END op_sorting_defn
```

In this case, the objects will sort lexigraphically based upon action result, thereby always producing "a" as the final decision.
