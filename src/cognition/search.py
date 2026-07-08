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

from .functypes import (
    Function,
    Predicate,
    Supplier,
)

from .utility import stringify

from .core import (
    Action,
    IOContainer,
    Task,
)

#

type PathCost = int | float
"""Cost of an action (can be whole numbers or decimal)"""


@dataclass(frozen=True, order=True)
class FrontierNode[SS, SA]:
    """
    Item on the search frontier
    """

    state: SS = field(compare=False)
    """state that would result"""

    path: Sequence[SA] = field(compare=False)
    """path of actions to achieve the state"""

    path_cost: PathCost
    """cost of the path to achieve the state"""


class Frontier[SS, SA](ABC):
    """
    Data structure to manage the search frontier
    """

    @property
    @abstractmethod
    def empty(self) -> bool:
        """
        :return: `True` if there are no more items on the frontier
        """

    @abstractmethod
    def add(self, node: FrontierNode[SS, SA]) -> None:
        """
        :param node: item to add to the frontier
        """

    @abstractmethod
    def remove(self) -> FrontierNode[SS, SA]:
        """
        :return: the next frontier item
        """

    @abstractmethod
    def __str__(self) -> str: ...


class Stack[SS, SA](Frontier[SS, SA]):
    """
    DFS frontier
    """

    _items: list[FrontierNode[SS, SA]]

    def __init__(self) -> None:
        self._items = []

    def __str__(self) -> str:
        return f"Stack(items={self._items})"

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        self._items.append(node)

    def remove(self) -> FrontierNode[SS, SA]:
        return self._items.pop()


class Queue[SS, SA](Frontier[SS, SA]):
    """
    BFS frontier
    """

    _items: deque[FrontierNode[SS, SA]]

    def __init__(self) -> None:
        self._items = deque()

    def __str__(self) -> str:
        return f"Queue(items={self._items})"

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        self._items.appendleft(node)

    def remove(self) -> FrontierNode[SS, SA]:
        return self._items.pop()


class PriorityQueue[SS, SA](Frontier[SS, SA]):
    """
    UCS frontier, or A* if given an admissible heuristic
    """

    _items: list[tuple[PathCost, FrontierNode[SS, SA]]]
    _heuristic: Optional[Function[SS, PathCost]]

    def __init__(self, heuristic: Optional[Function[SS, PathCost]] = None) -> None:
        """
        :param heuristic: if supplied, provides an estimate of remaining cost
        """

        self._items = []
        self._heuristic = heuristic

    def __str__(self) -> str:
        return (
            "PriorityQueue(" f"heuristic={self._heuristic}, " f"items={self._items}" ")"
        )

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[SS, SA]) -> None:
        node_priority: PathCost = node.path_cost
        if self._heuristic:
            node_priority += self._heuristic(node.state)

        heapq.heappush(self._items, (node_priority, node))

    def remove(self) -> FrontierNode[SS, SA]:
        return heapq.heappop(self._items)[1]


type Succession[S, A] = Function[S, Iterable[tuple[S, A, PathCost]]]
"""Given a search state, produces (state', action, cost) triple(s)"""


@dataclass
class SearchState[SS: Hashable, SA]:
    """
    Internal representation of a search task
    """

    explored: set[SS]
    """states already explored"""

    frontier: Frontier[SS, SA]
    """states to be explored"""

    done: bool
    """``True`` if done searching"""

    final_state: Optional[SS]
    """final state, or None if failure"""

    action_path: Optional[Sequence[SA]]
    """sequence of actions to the final state, or None if failure"""

    path_cost: Optional[PathCost]
    """cost of actions to the final state, or None if failure"""

    def failure(self) -> None:
        """Frontier has been exhausted"""

        self.done = True

    def success(self, node: FrontierNode[SS, SA]) -> None:
        """
        Goal state found

        :param node: identified goal state
        """

        self.done = True
        self.final_state = node.state
        self.action_path = node.path
        self.path_cost = node.path_cost

    def __str__(self) -> str:
        return (
            "SearchState("
            f"explored={self.explored}, "
            f"frontier={str(self.frontier)}, "
            f"done={self.done}, "
            f"final_state={self.final_state}, "
            f"action_path={self.action_path}, "
            f"path_cost={self.path_cost}"
            ")"
        )


def create_search_task[SS: Hashable, SA](
    initial_state: SS,
    is_goal: Predicate[SS],
    successors: Succession[SS, SA],
    frontier_factory: Supplier[Frontier[SS, SA]] = PriorityQueue,
) -> Task[SearchState[SS, SA]]:
    """
    Produce a search-based planner

    :param initial_state: starting node
    :param is_goal: goal predicate
    :param successors: function to produce node transitions
    :param frontier_factory: function to produce prioritize frontier nodes
    :return: graph-search task
    """

    @stringify("init_search")
    def init_task_state() -> SearchState[SS, SA]:
        """Initialize search problem"""

        init_frontier = frontier_factory()
        init_frontier.add(FrontierNode(initial_state, tuple(), 0))

        return SearchState[SS, SA](
            explored=set(),
            frontier=init_frontier,
            done=False,
            final_state=None,
            action_path=None,
            path_cost=None,
        )

    t: Task[SearchState[SS, SA]] = Task(init_task_state)

    #

    @t.action_factory
    @stringify("always_search")
    def search_factory(
        _s: SearchState[SS, SA], _io: IOContainer
    ) -> Action[SearchState[SS, SA]]:
        """Always propose searching"""

        @stringify("search")
        def search_action(sa: SearchState[SS, SA], _io: IOContainer) -> None:
            """Graph search step"""

            if sa.frontier.empty:
                return sa.failure()

            node = sa.frontier.remove()

            if is_goal(node.state):
                return sa.success(node)

            if node.state not in sa.explored:
                sa.explored.add(node.state)

                for state_p, action, cost in successors(node.state):
                    sa.frontier.add(
                        FrontierNode(
                            state=state_p,
                            path=(tuple(node.path) + (action,)),
                            path_cost=node.path_cost + cost,
                        )
                    )

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

    return t


class SearchOption[SS, SA](ABC):
    """
    A transition applicable to many search states
    """

    def __init__(self, action: SA) -> None:
        """
        :param action: action that might be performed in multiple contexts
        """

        self._action = action

    @property
    def action(self) -> SA:
        """
        :return: associated action
        """

        return self._action

    @abstractmethod
    def available(self, state: SS) -> bool:
        """
        State-gating predicate

        :param state: state to consider
        :return: ``True`` if action applies
        """

    @abstractmethod
    def invoke(self, state: SS) -> tuple[SS, PathCost]:
        """
        Applies the action

        :param state: starting state
        :return: resulting state and cost from applying the action
        """


def succession_via_options[SS, SA](
    *options: SearchOption[SS, SA]
) -> Succession[SS, SA]:
    """
    Succession function from options

    :param options: globally available transitions
    :return: resulting succession function for any search state
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

                yield (state_p, opt.action, cost)

    return expand
