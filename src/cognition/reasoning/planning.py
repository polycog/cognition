"""
Planning support
"""

from typing import Optional, Self

from abc import abstractmethod, ABC
from dataclasses import dataclass, field

from collections import deque

from collections.abc import (
    Hashable,
    Iterable,
    Sequence,
)

import heapq

from ..util.functypes import (
    Function,
    Predicate,
    Supplier,
)

from ..util.misc import stringify

from ..decision.core import (
    Action,
    IOContainer,
    Task,
)

#

type PathCost = int | float
"""Cost of an action (can be whole numbers or decimal)"""


@dataclass(frozen=True, order=True)
class FrontierNode[PS, PA]:
    """
    Item on the planning frontier
    """

    state: PS = field(compare=False)
    """state that would result"""

    path: Sequence[PA] = field(compare=False)
    """path of actions to achieve the state"""

    path_cost: PathCost
    """cost of the path to achieve the state"""


class FrontierManager[PS, PA](ABC):
    """
    Data structure to manage the planning frontier
    """

    @property
    @abstractmethod
    def empty(self) -> bool:
        """
        :return: `True` if there are no more items on the frontier
        """

    @abstractmethod
    def add(self, node: FrontierNode[PS, PA]) -> None:
        """
        :param node: item to add to the frontier
        """

    @abstractmethod
    def remove(self) -> FrontierNode[PS, PA]:
        """
        :return: the next frontier item
        """

    @abstractmethod
    def __str__(self) -> str: ...


class Stack[PS, PA](FrontierManager[PS, PA]):
    """
    DFS frontier
    """

    _items: list[FrontierNode[PS, PA]]

    def __init__(self) -> None:
        self._items = []

    def __str__(self) -> str:
        return f"Stack(items={self._items})"

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[PS, PA]) -> None:
        self._items.append(node)

    def remove(self) -> FrontierNode[PS, PA]:
        return self._items.pop()


class Queue[PS, PA](FrontierManager[PS, PA]):
    """
    BFS frontier
    """

    _items: deque[FrontierNode[PS, PA]]

    def __init__(self) -> None:
        self._items = deque()

    def __str__(self) -> str:
        return f"Queue(items={self._items})"

    @property
    def empty(self) -> bool:
        return not self._items

    def add(self, node: FrontierNode[PS, PA]) -> None:
        self._items.appendleft(node)

    def remove(self) -> FrontierNode[PS, PA]:
        return self._items.pop()


class PriorityQueue[PS, PA](FrontierManager[PS, PA]):
    """
    UCS frontier, or A* if given an admissible heuristic
    """

    _items: list[tuple[PathCost, FrontierNode[PS, PA]]]
    _heuristic: Optional[Function[PS, PathCost]]

    def __init__(self, heuristic: Optional[Function[PS, PathCost]] = None) -> None:
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

    def add(self, node: FrontierNode[PS, PA]) -> None:
        node_priority: PathCost = node.path_cost
        if self._heuristic:
            node_priority += self._heuristic(node.state)

        heapq.heappush(self._items, (node_priority, node))

    def remove(self) -> FrontierNode[PS, PA]:
        return heapq.heappop(self._items)[1]


type Succession[S, A] = Function[S, Iterable[tuple[S, A, PathCost]]]
"""Given a planning state, produces (state', action, cost) triple(s)"""


@dataclass
class SearchState[PS: Hashable, PA]:
    """
    Internal representation for search-based planning
    """

    explored: set[PS]
    """states already explored"""

    frontier: FrontierManager[PS, PA]
    """states to be explored"""

    done: bool
    """``True`` if done searching"""

    final_state: Optional[PS]
    """final state, or None if failure"""

    action_path: Optional[Sequence[PA]]
    """sequence of actions to the final state, or None if failure"""

    path_cost: Optional[PathCost]
    """cost of actions to the final state, or None if failure"""

    def failure(self) -> None:
        """Frontier has been exhausted"""

        self.done = True

    def success(self, node: FrontierNode[PS, PA]) -> None:
        """
        Goal state found

        :param node: identified goal state
        """

        self.done = True
        self.final_state = node.state
        self.action_path = node.path
        self.path_cost = node.path_cost

    def __str__(self) -> str:  # pragma: no cover
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


class SearchPlanner[PS: Hashable, PA]:
    """
    A planner that iteratively produces an action
    plan by searching the space of states produced
    via a succession function starting from an
    initial state until the goal predicate is satisfied
    (or all possible options have been exhausted).
    """

    @staticmethod
    def _create_search_task(
        initial_state: PS,
        is_goal: Predicate[PS],
        successors: Succession[PS, PA],
        frontier_factory: Supplier[FrontierManager[PS, PA]],
    ) -> Task[SearchState[PS, PA]]:
        """
        Produce a search-based planner task

        :param initial_state: starting node
        :param is_goal: goal predicate
        :param successors: function to produce node transitions
        :param frontier_factory: function to produce prioritize frontier nodes
        :return: graph-search task
        """

        @stringify("init_search")
        def init_task_state() -> SearchState[PS, PA]:
            """Initialize search problem"""

            init_frontier = frontier_factory()
            init_frontier.add(FrontierNode(initial_state, tuple(), 0))

            return SearchState[PS, PA](
                explored=set(),
                frontier=init_frontier,
                done=False,
                final_state=None,
                action_path=None,
                path_cost=None,
            )

        t: Task[SearchState[PS, PA]] = Task(init_task_state)

        #

        @t.action_factory
        @stringify("always_search")
        def search_factory(
            _s: SearchState[PS, PA], _io: IOContainer
        ) -> Action[SearchState[PS, PA]]:
            """Always propose searching"""

            @stringify("search")
            def search_action(sa: SearchState[PS, PA], _io: IOContainer) -> None:
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

        @t.termination_check
        @stringify("search_complete")
        def search_complete(
            s: SearchState[PS, PA],
            _io: IOContainer,
        ) -> bool:
            """done searching?"""

            return s.done

        return t

    def __init__(
        self,
        initial_state: PS,
        is_goal: Predicate[PS],
        successors: Succession[PS, PA],
        frontier_factory: Supplier[FrontierManager[PS, PA]] = PriorityQueue,
    ) -> None:
        """
        :param initial_state: starting node
        :param is_goal: goal predicate
        :param successors: function to produce node transitions
        :param frontier_factory: function to prioritize frontier nodes
        """

        self._t = SearchPlanner._create_search_task(
            initial_state, is_goal, successors, frontier_factory
        )

    @property
    def still_searching(self) -> bool:
        """
        Indicates if the planner still has options to explore.

        :return: `True` if the planner has not concluded search
        """

        return not self._t.done

    def run(self, max_steps: Optional[int] = None) -> Self:
        """
        Attempts to search for a solution.

        :param max_steps: if supplied, maximum number of planner steps to expend before returning
        :return: this planner (for chaining)
        """

        if max_steps is None:
            self._t.run_until_done()
        else:
            self._t.run_cycles(max_steps)

        return self

    @property
    def plan_found(self) -> bool:
        """
        Indicates if a plan was found.

        :return: `True` if the planner was successful
        """

        return self._t.state.final_state is not None

    @property
    def plan(self) -> Sequence[PA]:
        """
        The found plan

        :raises RuntimeError: plan not available
        :return: sequence of actions to the final state
        """

        if self._t.state.action_path is None:
            raise RuntimeError("Plan not available")

        return self._t.state.action_path

    @property
    def plan_cost(self) -> PathCost:
        """
        Cost of the found plan

        :raises RuntimeError: plan not available
        :return: cost of path actions
        """

        if self._t.state.path_cost is None:
            raise RuntimeError("Plan not available")

        return self._t.state.path_cost

    @property
    def states_explored(self) -> int:
        """
        Number of states explored thus
        far during planning (roughly
        correlating with effort)

        :return: number of states explored
        """

        return len(self._t.state.explored)


class SearchPlannerOption[PS, PA](ABC):
    """
    A transition applicable to many states
    """

    def __init__(self, action: PA) -> None:
        """
        :param action: action that might be performed in multiple contexts
        """

        self._action = action

    @property
    def action(self) -> PA:
        """
        :return: associated action
        """

        return self._action

    @abstractmethod
    def available(self, state: PS) -> bool:
        """
        State-gating predicate

        :param state: state to consider
        :return: ``True`` if action applies
        """

    @abstractmethod
    def invoke(self, state: PS) -> tuple[PS, PathCost]:
        """
        Applies the action

        :param state: starting state
        :return: resulting state and cost from applying the action
        """


def succession_via_options[PS, PA](
    *options: SearchPlannerOption[PS, PA]
) -> Succession[PS, PA]:
    """
    Succession function from options

    :param options: globally available transitions
    :return: resulting succession function for any search state
    """

    fixed_opts = tuple(options)

    def expand(s: PS) -> Iterable[tuple[PS, PA, PathCost]]:
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
