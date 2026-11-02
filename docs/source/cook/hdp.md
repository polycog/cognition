# Hierarchical Decision Processes

Similar to how complex programs are decomposed into functions, a complex [](../ideas/kadp.md) is often decomposed into multiple DPs.
Since a [](../ideas/cogent.md) has a single "root" DP, process decomposition thus naturally produces a hierarchy.
And as with function decomposition, hierarchical DPs commonly produces multiple benefits, including...

* DP re-use: a single decision process can be called upon in multiple contexts, possibly with re-parameterization (e.g., via supplied arguments)
* State/logic simplification: each sub-process focuses solely on those state features that are necessary
  * As a bi-product, testing becomes simplified as well!

In the code below, an agent assists a [Bingo](https://en.wikipedia.org/wiki/Bingo_(American_version)) caller in keeping track of drawn balls:

```{literalinclude} src/hdp.py
:linenos:
```

## Root DP: Ball Draw <-> Game-Win Verification

The cogent primarily operates within a logical loop:

1. Call the next drawn ball
   1. Verified as a valid letter-number combination
   2. Confirmed as not having been called before
2. If "Bingo!" is claimed, providing prior draws for confirmation
   1. If confirmed, done
   2. Otherwise, back to #1

This is encoded as the `dp_play` DP.

:::{tip}
In practice, decision process decomposition invites decomposition into separate files/folders (e.g., folder for the DP, with files for state, operators, support functions, etc.).
:::


## Sub-Process: Validate Call (1.1)

Nested within the root DP is the need to verify a valid letter and associated number:

```{literalinclude} src/hdp.py
:start-after: START valid_bounds
:end-before: END valid_bounds
```

Errors include...
* An invalid letter
* Given a letter, an invalid number
* A previously called combination (signaling full re-entry needed for a typo that produced a valid combination)

This sub-process is encapsulated within a function...

```{literalinclude} src/hdp.py
:start-after: START encapsulate
:end-before: END encapsulate
```

The `letter` argument parameterizes the `dp_input` DP's operators:
* The `GetInput` operator's prompt ("letter" vs "number")
* The choice of validation operator (via `can_perform`): `ValidateInputLetter` vs `ValidateInputNumber`

This function is called within the `perform` method of the root DP's `PlayDraw` operator.

### Sub-Process Testing

Since the sub-process is designed to be self-contained, requiring only a single argument, it is straightforward to test:

```{literalinclude} src/hdp.py
:start-after: START sub_problem_testing
:end-before: END sub_problem_testing
```

:::{note}
This very well could have been done within a standard testing framework (e.g., `unittest`, `pytest`) -- the code here is illustrative of the underlying IO mocking and self-contained.
:::
