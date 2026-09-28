# Hello World

We begin with a simple cogent that prints and then stops...

```{literalinclude} src/hello.py
:linenos:
```

## Low-Level

For those interested in the details of how this is equivalently implemented using core primitives...

```{literalinclude} src/hello_low.py
:linenos:
```

Notes...
* The `BaseDecisionProcess` utilizes `ActionFactory` to identify what `Action`(s) are appropriate in the current context.
  * Notice how an `Operator` facilitates a clean separation of proposal vs application logic: `Operator` provides a predicate (`can_perform`) to control proposal of a singular `Action` instantiation, `OperatorGenerator` provides flexibility (via `generate`) to dynamically propose multiple instantiation(s).
* The `terminal` flag of an instantiated `Operator` avoids duplicating the logic of `Action` post-conditions within a custom `TerminationCheck`.
* Without any sensors/actuators, the `Cogent` serves largely as a wrapper around the supplied DP.
* While not necessary for function, the `stringify` decorator provides objects a user-friendly `str()` result.
  * This is particularly helpful when examining a DP (via `print`).
