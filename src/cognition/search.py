"""
Support for a task generated
via a Search problem.
"""

from typing import Optional

from abc import abstractmethod, ABC
from dataclasses import dataclass, field

from collections import deque

from collections.abc import (
    Hashable,
    Iterable,
    Sequence,
)

import heapq

from cognition.functypes import (
    Function,
    Predicate,
    Supplier,
)

from cognition.utility import stringify

from cognition.core import (
    Action,
    IOContainer,
    Task,
)

#

# Action costs can be whole numbers or decimal
type PathCost = int | float


@dataclass(frozen=True, order=True)
class FrontierNode[SS, SA]:
    """
    Item on the search frontier, including
    both the next state and path of actions
    to achieve that state from initial
    (as well as the cost of that path)
    """

    state: SS = field(compare=False)
    path: Sequence[SA] = field(compare=False)
    path_cost: PathCost


class Frontier[SS, SA](ABC):
    """
	Abstraction over management of options
	for a graph search
    """

    @property
    @abstractmethod
    def empty(self) -> bool:
        """
        Returns true if there are no more items
        on the frontier
        """

    @abstractmethod
    def add(self, node: FrontierNode[SS, SA]) -> None:
        """
        Adds an item to the frontier
        """

    @abstractmethod
    def remove(self) -> FrontierNode[SS, SA]:
        """
        Provides the next frontier item
        """

    @abstractmethod
    def __str__(self) -> str:
        """
        Provides human-readable view
        """

class Stack[SS, SA](Frontier[SS, SA]):
    """
    Produces DFS behavior
    """

    _items: list[FrontierNode[SS, SA]]

    def __init__(self) -> None:
        self._items = []

    def __str__(self) -> str: # pragma: no cover
        return (
            "Stack("
            f"items=[{self._items}]"
            ")"
        )

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        self._items.append(node)

    def remove(self) -> FrontierNode[SS, SA]:
        return self._items.pop()

class Queue[SS, SA](Frontier[SS, SA]):
    """
    Produces BFS behavior
    """

    _items: deque[FrontierNode[SS, SA]]

    def __init__(self) -> None:
        self._items = deque()

    def __str__(self) -> str: # pragma: no cover
        return (
            "Queue("
            f"items=[{self._items}]"
            ")"
        )

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        self._items.appendleft(node)

    def remove(self) -> FrontierNode[SS, SA]:
        return self._items.pop()

class PriorityQueue[SS, SA](Frontier[SS, SA]):
    """
    Produces UCS behavior, or A*
    given an optional heuristic
    (which is assumed to be
    admissible!)
    """

    _items: list[
        tuple[
            PathCost,
            FrontierNode[SS, SA]
        ]
    ]
    _heuristic: Optional[Function[SS, PathCost]]

    def __init__(
        self,
        heuristic: Optional[Function[SS, PathCost]] = None
    ) -> None:
        self._items = []
        self._heuristic = heuristic

    def __str__(self) -> str: # pragma: no cover
        return (
            "PriorityQueue("
            f"heuristic=[{self._heuristic}], "
            f"items=[{self._items}]"
            ")"
        )

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        node_priority: PathCost = node.path_cost
        if self._heuristic:
            node_priority += self._heuristic(node.state)

        heapq.heappush(
            self._items,
            (node_priority, node)
        )

    def remove(self) -> FrontierNode[SS, SA]:
        return heapq.heappop(self._items)[1]


# Function-like type that represents the
# successor function of a problem:
# Successor(S) = [State', Action, Cost]
type Succession[S, A] = Function[S, Iterable[tuple[S, A, PathCost]]]


@dataclass
class SearchState[SS: Hashable, SA]:
    """
    Internal representation of a search task
    """

    # states already explored
    explored: set[SS]

    # prioritized states to be explored
    frontier: Frontier[SS, SA]

    # True if done searching
    done: bool

    # final state, or None if failure
    final_state: Optional[SS]

    # sequence of actions to the final state, or None if failure
    action_path: Optional[Sequence[SA]]

    # cost of actions to the final state, or None if failure
    path_cost: Optional[PathCost]

    def failure(self) -> None:
        """Frontier has been exhausted"""
        self.done = True

    def success(self, node: FrontierNode[SS, SA]) -> None:
        """Goal state found in supplied node"""

        self.done = True
        self.final_state = node.state
        self.action_path = node.path
        self.path_cost = node.path_cost

    def __str__(self) -> str: # pragma: no cover
        return (
            "SearchState("
            f"explored=[{self.explored}], "
            f"frontier=[{str(self.frontier)}], "
            f"done=[{self.done}], "
            f"final_state=[{self.final_state}], "
            f"action_path=[{self.action_path}], "
            f"path_cost=[{self.path_cost}]"
            ")"
        )

def create_search_task[SS: Hashable, SA](
    initial_state: SS,
    is_goal: Predicate[SS],
    successors: Succession[SS, SA],
    frontier_factory: Supplier[Frontier[SS, SA]] = PriorityQueue,
    debug: bool = False
) -> Task[SearchState[SS, SA]]:
    """
    Produces a graph-search task given...
    * the initial problem state
    * a goal-detection function
    * a function to produce all successors
      of a given state
    * a way to produce the desired data
      structure to maintain the ordering
      of actions to explore
    """

    @stringify("init_search")
    def init_task_state() -> SearchState[SS, SA]:
        """Initialize search problem"""

        init_frontier = frontier_factory()
        init_frontier.add(
            FrontierNode(
                initial_state,
                tuple(),
                0
            )
        )

        return SearchState[SS, SA](
            explored=set(),
            frontier=init_frontier,

            done=False,

            final_state=None,
            action_path=None,
            path_cost=None
        )

    t: Task[SearchState[SS, SA]] = Task(init_task_state)

    #

    @t.action_factory
    @stringify("always_search")
    def search_factory(
        _s: SearchState[SS, SA],
        _io: IOContainer
    ) -> Action[SearchState[SS, SA]]:
        """Always propose searching"""

        @stringify("search")
        def search_action(
            sa: SearchState[SS, SA],
            io: IOContainer
        ) -> None:
            """Graph search step"""

            if sa.frontier.empty:
                return sa.failure()

            node = sa.frontier.remove()
            if debug: # pragma: no cover
                print(
                    f"Graph Search: remove ({node})",
                    file=io.o.log
                )

            if is_goal(node.state):
                if debug: # pragma: no cover
                    print(
                        f"Graph Search: goal achieved ({node})",
                        file=io.o.log
                    )
                return sa.success(node)

            if node.state not in sa.explored:
                sa.explored.add(node.state)
                if debug: # pragma: no cover
                    print(
                        "Graph Search: unexplored "
                        f"({node.state}) -> |{len(sa.explored)}|",
                        file=io.o.log
                    )

                for state_p, action, cost in successors(node.state):
                    if debug: # pragma: no cover
                        print(
                            f"Graph Search: add ({state_p}, {action}, {cost})",
                            file=io.o.log
                        )
                    sa.frontier.add(FrontierNode(
                        state=state_p,
                        path=(tuple(node.path) + (action,)),
                        path_cost=node.path_cost + cost
                    ))

            return None

        return search_action

    @t.goal_check
    @stringify("search_complete")
    def search_complete(
        s: SearchState[SS, SA],
        _io: IOContainer,
    ) -> bool:
        """done searching?"""

        return s.done

    # t.set_sensor(
    #     "problem",
    #     AttrReferral({
    #         "init_state": initial_state,
    #     })
    # )

    return t


class SearchOption[SS, SA](ABC):
    """
    Convenience abstraction for a search
    action that is generally available
    """

    def __init__(self, action: SA) -> None:
        """
        Initializes the option
        """

        self._action = action

    @property
    def action(self) -> SA:
        """
        Search action associated
        with this option
        """

        return self._action

    @abstractmethod
    def available(self, state: SS) -> bool:
        """
        Indicates if the option is
        permissible in the supplied
        search state
        """

    @abstractmethod
    def invoke(self, state: SS) -> tuple[SS, PathCost]:
        """
        Returns the search state resulting
        from invoking the option, as well
        as the associated invocation cost
        """

def succession_via_options[SS, SA](*options: SearchOption[SS, SA]) -> Succession[SS, SA]:
    """
    Convenience succession-generator via a set
    of globally available options
    """

    fixed_opts = tuple(options)

    def expand(s: SS) -> Iterable[tuple[SS, SA, PathCost]]:
        """
        Generic expansion function based
        upon a supplied fixed set of
        globally available options
        """

        for opt in fixed_opts:
            if opt.available(s):
                state_p, cost = opt.invoke(s)

                yield (
                    state_p,
                    opt.action,
                    cost
                )

    return expand
