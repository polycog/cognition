"""
Tests for planning code
"""

from __future__ import annotations

from typing import cast

from enum import IntEnum

from collections import Counter

from collections.abc import Iterable

import unittest

from cognition import (
    FrontierManager,
    FrontierNode,
    PriorityQueue,
    Queue,
    SearchPlanner,
    SearchPlannerDynamicOption,
    SearchPlannerStaticOption,
    Stack,
    Succession,
    Supplier,
    dynamic_opts_succession,
    stringify,
    static_opts_succession,
)

#


class TestFrontier(unittest.TestCase):
    """Tests frontier data structures"""

    def setUp(self) -> None:
        """Common testing info"""

        self.nodes = [
            FrontierNode(3, ("three",), 5),
            FrontierNode(2, ("two",), 3),
            FrontierNode(0, ("zero",), 4),
        ]

    def test_stack(self) -> None:
        """testing stack code"""

        ds: FrontierManager[int, str] = Stack()

        #

        self.assertEqual(str(ds), "Stack(items=[])")
        self.assertTrue(ds.empty)

        #

        for n in self.nodes:
            ds.add(n)

        self.assertEqual(
            str(ds), f"Stack(items=[{self.nodes[0]}, {self.nodes[1]}, {self.nodes[2]}])"
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[2])
        self.assertEqual(str(ds), f"Stack(items=[{self.nodes[0]}, {self.nodes[1]}])")
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[1])
        self.assertEqual(str(ds), f"Stack(items=[{self.nodes[0]}])")
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[0])
        self.assertEqual(str(ds), "Stack(items=[])")
        self.assertTrue(ds.empty)

    def test_queue(self) -> None:
        """testing queue code"""

        ds: FrontierManager[int, str] = Queue()

        #

        self.assertEqual(str(ds), "Queue(items=deque([]))")
        self.assertTrue(ds.empty)

        #

        for n in self.nodes:
            ds.add(n)

        self.assertEqual(
            str(ds),
            f"Queue(items=deque([{self.nodes[2]}, {self.nodes[1]}, {self.nodes[0]}]))",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[0])
        self.assertEqual(
            str(ds),
            f"Queue(items=deque([{self.nodes[2]}, {self.nodes[1]}]))",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[1])
        self.assertEqual(
            str(ds),
            f"Queue(items=deque([{self.nodes[2]}]))",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[2])
        self.assertEqual(
            str(ds),
            "Queue(items=deque([]))",
        )
        self.assertTrue(ds.empty)

    def test_pq(self) -> None:
        """testing priority queue code"""

        ds: FrontierManager[int, str] = PriorityQueue()

        #

        self.assertEqual(str(ds), "PriorityQueue(heuristic=None, items=[])")
        self.assertTrue(ds.empty)

        #

        for n in self.nodes:
            ds.add(n)

        def _seq(indices: list[int]) -> str:
            return ", ".join(
                str((self.nodes[idx].path_cost, self.nodes[idx])) for idx in indices
            )

        self.assertEqual(
            str(ds),
            f"PriorityQueue(heuristic=None, items=[{ _seq([1, 0, 2]) }])",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[1])
        self.assertEqual(
            str(ds),
            f"PriorityQueue(heuristic=None, items=[{ _seq([2, 0]) }])",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[2])
        self.assertEqual(
            str(ds),
            f"PriorityQueue(heuristic=None, items=[{ _seq([0]) }])",
        )
        self.assertFalse(ds.empty)

        #

        n = ds.remove()

        self.assertEqual(n, self.nodes[0])
        self.assertEqual(str(ds), "PriorityQueue(heuristic=None, items=[])")
        self.assertTrue(ds.empty)


def navigate_romania(city: str) -> Iterable[tuple[str, str, int]]:
    """
    Encodes the classic Romania map search from R&N
    """

    romania_map: dict[str, dict[str, int]] = {
        "Arad": {"Zerind": 75, "Timisoara": 118, "Sibiu": 140},
        "Zerind": {"Arad": 75, "Oradea": 71},
        "Oradea": {"Zerind": 71, "Sibiu": 151},
        "Timisoara": {"Arad": 118, "Lugoj": 111},
        "Lugoj": {"Timisoara": 111, "Mehadia": 70},
        "Mehadia": {"Lugoj": 70, "Drobeta": 75},
        "Drobeta": {"Mehadia": 75, "Craiova": 120},
        "Craiova": {"Drobeta": 120, "Rimnicu Vilcea": 146, "Pitesti": 138},
        "Sibiu": {"Arad": 140, "Oradea": 151, "Fagaras": 99, "Rimnicu Vilcea": 80},
        "Rimnicu Vilcea": {"Sibiu": 80, "Craiova": 146, "Pitesti": 97},
        "Fagaras": {"Sibiu": 99, "Bucharest": 211},
        "Pitesti": {"Rimnicu Vilcea": 97, "Craiova": 138, "Bucharest": 101},
        "Bucharest": {"Fagaras": 211, "Pitesti": 101, "Giurgiu": 90, "Urziceni": 85},
        "Giurgiu": {"Bucharest": 90},
        "Urziceni": {"Bucharest": 85, "Vaslui": 142, "Hirsova": 98},
        "Vaslui": {"Urziceni": 142, "Iasi": 92},
        "Iasi": {"Vaslui": 92, "Neamt": 87},
        "Neamt": {"Iasi": 87},
        "Hirsova": {"Urziceni": 98, "Eforie": 86},
        "Eforie": {"Hirsova": 86},
    }

    # keep the (unnecessary) sorting to see
    # differences in stack vs queue vs pq
    for c, d in sorted(romania_map.get(city, {}).items()):
        yield c, c, d


@stringify("straight_line_to_bucharest")
def straight_line_to_bucharest(city: str) -> int:
    """
    Encodes the straight-line distances in Romania
    (city -> Bucharest) from R&N
    """

    return {
        "Arad": 366,
        "Bucharest": 0,
        "Craiova": 160,
        "Dobreta": 242,
        "Eforie": 161,
        "Fagaras": 176,
        "Giurgiu": 77,
        "Hirsova": 151,
        "Iasi": 226,
        "Lugoj": 244,
        "Mehadia": 241,
        "Neamti": 234,
        "Oradea": 380,
        "Pitesti": 100,
        "Rimnicu Vilcea": 193,
        "Sibiu": 253,
        "Timisoara": 329,
        "Urziceni": 80,
        "Vaslui": 199,
        "Zerind": 374,
    }.get(city, 1000)


def in_bucharest(city: str) -> bool:
    """Is this Bucharest?"""

    return city == "Bucharest"


class TestSearchPlanning(unittest.TestCase):
    """Tests search planner code"""

    def setUp(self) -> None:
        """Common testing info"""

        self.initial_state: str = "Arad"

    def test_romania_exhaustion(self) -> None:
        """testing search across Romania without achievable goal"""

        planner = SearchPlanner(
            self.initial_state,
            lambda city: city == "does not exist",
            navigate_romania,
            Stack,
        )

        # there are 20 distinct cities,
        # so assuming you can get to all
        # of them from start city...
        planner.run(max_steps=18)
        self.assertTrue(planner.still_searching)

        planner.run()

        self.assertFalse(planner.still_searching)
        self.assertEqual(planner.states_explored, 20)

        self.assertFalse(planner.plan_found)

        with self.assertRaises(RuntimeError):
            _ = planner.plan

        with self.assertRaises(RuntimeError):
            _ = planner.plan_cost

    def _test_success(
        self,
        ds: Supplier[FrontierManager[str, str]],
        expected_explored: int,
        expected_cost: int,
        expected_plan: list[str],
    ) -> None:
        """
        common testing code across frontiers
        (given successful parameters)
        """

        planner = SearchPlanner(
            self.initial_state, in_bucharest, navigate_romania, ds
        ).run()

        self.assertFalse(planner.still_searching)
        self.assertEqual(planner.states_explored, expected_explored)

        self.assertTrue(planner.plan_found)
        self.assertEqual(cast(int, planner.plan_cost), expected_cost)
        self.assertSequenceEqual(
            planner.plan,
            expected_plan,
        )

    def test_romania_dfs(self) -> None:
        """testing search across Romania using DFS"""

        self._test_success(
            Stack,
            11,
            575,
            ["Zerind", "Oradea", "Sibiu", "Rimnicu Vilcea", "Pitesti", "Bucharest"],
        )

    def test_romania_bfs(self) -> None:
        """testing search across Romania using BFS"""

        self._test_success(Queue, 8, 450, ["Sibiu", "Fagaras", "Bucharest"])

    def test_romania_ucs(self) -> None:
        """testing search across Romania using UCS"""

        self._test_success(
            PriorityQueue, 12, 418, ["Sibiu", "Rimnicu Vilcea", "Pitesti", "Bucharest"]
        )

    def test_romania_astar(self) -> None:
        """testing search across Romania using A*"""

        self._test_success(
            lambda: PriorityQueue(straight_line_to_bucharest),
            5,
            418,
            ["Sibiu", "Rimnicu Vilcea", "Pitesti", "Bucharest"],
        )


#


class USCoin(IntEnum):
    """US coin name/value"""

    QUARTER = 25
    DIME = 10
    NICKLE = 5
    PENNY = 1


class AddCoinStatic(SearchPlannerStaticOption[int, USCoin]):
    """Option to add a coin"""

    def __init__(self, coin: USCoin):
        super().__init__(coin)

    def available(self, _: int) -> bool:
        return True

    def then(self, state: int) -> tuple[int, int]:
        return (state + self.action.value, 1)


class AddCoinDynamic(SearchPlannerDynamicOption[int, USCoin]):
    """Option to add a coin"""

    def __init__(self, coin: USCoin):
        super().__init__(coin)

    @classmethod
    def when(cls, _state: int) -> Iterable[AddCoinDynamic]:
        yield from (AddCoinDynamic(c) for c in USCoin)

    def then(self, state: int) -> tuple[int, int]:
        return (state + self.action.value, 1)


class TestPlanningOptions(unittest.TestCase):
    """
    Use planning options
    to solve smallest change via coins
    """

    def setUp(self) -> None:
        """Common testing info"""

        self.init_cents: int = 0

        goal_cents: int = 119
        self.termination_test = lambda s: s == goal_cents

        self.frontier_factory = Queue
        # each coin is a single action
        # and queue = BFS, so...
        # produces sum with fewest coins

        self.opt_plan_cost: int = 10
        self.opt_plan = {
            USCoin.QUARTER: 4,  # 100 +
            USCoin.DIME: 1,  #     10 +
            USCoin.NICKLE: 1,  #    5 +
            USCoin.PENNY: 4,  #     4
        }  #                    = 119

    def _test_planner(self, sf: Succession[int, USCoin]) -> None:
        """Common assertions"""

        planner = SearchPlanner(
            self.init_cents,
            self.termination_test,
            sf,
            self.frontier_factory,
        )

        planner.run()

        self.assertFalse(planner.still_searching)

        self.assertTrue(planner.plan_found)
        self.assertEqual(planner.plan_cost, self.opt_plan_cost)
        self.assertDictEqual(dict(Counter(planner.plan)), self.opt_plan)

    def test_static(self) -> None:
        """Static options"""

        self._test_planner(static_opts_succession(*(AddCoinStatic(c) for c in USCoin)))

    def test_dynamic(self) -> None:
        """Dynamic options"""

        self._test_planner(dynamic_opts_succession(AddCoinDynamic))
