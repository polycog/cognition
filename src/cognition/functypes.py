"""
Functional types

ala
https://docs.oracle.com/javase/8/docs/api/java/util/function/package-summary.html
"""

from collections.abc import Callable

#

type Supplier[X] = Callable[[], X]
type Function[X, Y] = Callable[[X], Y]
type BiFunction[X, Y, Z] = Callable[[X, Y], Z]
type TriFunction[X, Y, Z, Q] = Callable[[X, Y, Z], Q]

type Consumer[X] = Function[X, None]
type BiConsumer[X, Y] = BiFunction[X, Y, None]

type Predicate[X] = Function[X, bool]
type BiPredicate[X, Y] = BiFunction[X, Y, bool]
