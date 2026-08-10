"""
Functional types

ala
https://docs.oracle.com/javase/8/docs/api/java/util/function/package-summary.html
"""

from collections.abc import Callable

# ===

type Supplier[X] = Callable[[], X]
"""Represents a supplier of results."""

type Function[X, Y] = Callable[[X], Y]
"""Represents a function that accepts one argument and produces a result."""

type BiFunction[X, Y, Z] = Callable[[X, Y], Z]
"""Represents a function that accepts two arguments and produces a result."""

type TriFunction[X, Y, Z, Q] = Callable[[X, Y, Z], Q]
"""Represents a function that accepts three arguments and produces a result."""

type Consumer[X] = Function[X, None]
"""Represents an operation that accepts a single input argument and returns no result."""

type BiConsumer[X, Y] = BiFunction[X, Y, None]
"""Represents an operation that accepts two input arguments and returns no result."""

type Predicate[X] = Function[X, bool]
"""Represents a predicate (boolean-valued function) of one argument."""

type BiPredicate[X, Y] = BiFunction[X, Y, bool]
"""Represents a predicate (boolean-valued function) of two arguments."""
