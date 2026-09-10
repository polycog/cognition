# Planning

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
