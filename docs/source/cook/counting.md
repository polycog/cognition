# Counting

In this recipe, we use a "counting" cogent to illustrate basic usage of a few library features:
* Elaboration: information, accessible via `IOContainer.e.feature_name`, that is computed each cycle (during the DP `Elaboration` phase)
  * `create_elaborator`: a convenience function for creating an `Elaborator` based upon kwargs that associate feature_name with a function to compute the associated value
* Termination Check: a function that (during the DP `TerminationCheck` phase) determines if the DP should end
* Arguments: name=value pairs supplied to a DP that are accessible via `IOContainer.a.name`
* Logging: using the standard Python `logging` library
  * Debug output: using the `stringify` function can improve readability of logs, as well as debug output (e.g., printing a DP)

## Detailed Run Summary
Let's focus on line `142`, assuming `starting_val` is `2`...
1. The value `2` is accessible via the `counting_start` argument (@ `io.a.counter_start`)
2. DP reinit (`state.counter` -> `None`); DP run!
    1. DP Cycle 1
        1. Elaboration: the union is taken of all the key-value pairs produced across all elaborators (which is just one in this example), yielding `{'is_initialized': False, 'is_perfect': False, 'as_str': 'None'}`
        2. TerminationCheck: if any check returns `True` (including selection of a `terminal` operator, by default), the DP stops; but not yet (since `found_perfect` finds that `io.e.is_perfect` is `False`)
        3. Propose: the operators are mutually exclusive (by design) and so `init` is proposed as the only action
        4. Rank: only one action, so `init` is selected
        5. Apply: `init` changes `state.counter` -> `2`
    2. Cycle 2
        1. Elaboration: `io.e` -> `{'is_initialized': True, 'is_perfect': False, 'as_str': '2'}`
        2. TerminationCheck: `False` (still going!)
        3. Propose: only `increment` is proposed
        4. Rank: only one action, so `increment` is selected
        5. Apply: `increment` changes `state.counter` -> `3`
    3. Cycle 3
        1. Elaboration: `io.e` -> `{'is_initialized': True, 'is_perfect': False, 'as_str': '3'}`
        2. TerminationCheck: `False` (still going!)
        3. Propose: only `increment` is proposed
        4. Rank: only one action, so `increment` is selected
        5. Apply: `increment` changes `state.counter` -> `4`
    4. Cycle 4
        1. Elaboration: `io.e` -> `{'is_initialized': True, 'is_perfect': True, 'as_str': '4'}`
        2. TerminationCheck: `True` (done!)
5. DP run complete; Cogent gate check (done!)
6. Arguments (`counting_start`) removed


## Code

```{literalinclude} src/counting.py
:linenos:
```
