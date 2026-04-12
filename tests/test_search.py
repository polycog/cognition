"""
Tests for search code
"""

from typing import (
    Iterable,
    Sequence,
    cast,
)

import unittest

from cognition import (
    PriorityQueue,
    Queue,
    Stack,
    create_search_task,
)

#

def navigate_romania(city: str) -> Iterable[tuple[str, str, int]]:
    """
    Encodes the classic Romania map search from R&N
    """

    romania_map: dict[str, dict[str, int]] = {
        'Arad': {'Zerind': 75, 'Timisoara': 118, 'Sibiu': 140},
        'Zerind': {'Arad': 75, 'Oradea': 71},
        'Oradea': {'Zerind': 71, 'Sibiu': 151},
        'Timisoara': {'Arad': 118, 'Lugoj': 111},
        'Lugoj': {'Timisoara': 111, 'Mehadia': 70},
        'Mehadia': {'Lugoj': 70, 'Drobeta': 75},
        'Drobeta': {'Mehadia': 75, 'Craiova': 120},
        'Craiova': {'Drobeta': 120, 'Rimnicu Vilcea': 146, 'Pitesti': 138},
        'Sibiu': {'Arad': 140, 'Oradea': 151, 'Fagaras': 99, 'Rimnicu Vilcea': 80},
        'Rimnicu Vilcea': {'Sibiu': 80, 'Craiova': 146, 'Pitesti': 97},
        'Fagaras': {'Sibiu': 99, 'Bucharest': 211},
        'Pitesti': {'Rimnicu Vilcea': 97, 'Craiova': 138, 'Bucharest': 101},
        'Bucharest': {'Fagaras': 211, 'Pitesti': 101, 'Giurgiu': 90, 'Urziceni': 85},
        'Giurgiu': {'Bucharest': 90},
        'Urziceni': {'Bucharest': 85, 'Vaslui': 142, 'Hirsova': 98},
        'Vaslui': {'Urziceni': 142, 'Iasi': 92},
        'Iasi': {'Vaslui': 92, 'Neamt': 87},
        'Neamt': {'Iasi': 87},
        'Hirsova': {'Urziceni': 98, 'Eforie': 86},
        'Eforie': {'Hirsova': 86},
    }

    # keep the (unnecessary) sorting to see
    # differences in stack vs queue vs pq
    for c, d in sorted(romania_map.get(city, {}).items()):
        yield c, c, d

def straight_line_to_bucharest(city: str) -> int:
    """
    Encodes the straight-line distances in Romania
    (city -> Bucharest) from R&N
    """

    return {
        'Arad': 366, 'Bucharest': 0, 'Craiova': 160, 'Dobreta': 242, 'Eforie': 161,
        'Fagaras': 176, 'Giurgiu': 77, 'Hirsova': 151, 'Iasi': 226, 'Lugoj': 244,
        'Mehadia': 241, 'Neamti': 234, 'Oradea': 380, 'Pitesti': 100, 'Rimnicu Vilcea': 193,
        'Sibiu': 253, 'Timisoara': 329, 'Urziceni': 80, 'Vaslui': 199, 'Zerind': 374
    }.get(city, 1000)

def in_bucharest(city: str) -> bool:
    """Is this Bucharest?"""

    return city == "Bucharest"

class TestSearch(unittest.TestCase):
    """Tests for search code"""

    def setUp(self) -> None:
        """Common testing info"""

        self.initial_state: str = "Arad"

    def test_romania_exhaustion(self) -> None:
        """testing search across Romania without achievable goal"""

        t = create_search_task(
            self.initial_state,
            lambda city: city == "does not exist",
            navigate_romania,
            Stack,
        )
        t.run_until_done()

        self.assertTrue(t.state.done)
        self.assertIsNone(t.state.path_cost)
        self.assertIsNone(t.state.action_path)
        self.assertIsNone(t.state.final_state)

        explored: int = len(t.state.explored)
        self.assertEqual(explored, 20)

        self.assertTrue(t.state.frontier.empty)


    def test_romania_dfs(self) -> None:
        """testing search across Romania using DFS"""

        t = create_search_task(
            self.initial_state,
            in_bucharest,
            navigate_romania,
            Stack,
            # debug=True
        )
        t.run_until_done()

        self.assertTrue(t.state.done)

        final: str = cast(str, t.state.final_state)
        self.assertEqual(final, "Bucharest")

        dist: int = cast(int, t.state.path_cost)
        self.assertEqual(dist, 575)

        explored: int = len(t.state.explored)
        self.assertEqual(explored, 11)

        self.assertFalse(t.state.frontier.empty)

        actions: Sequence[str] = cast(
            Sequence[str],
            t.state.action_path
        )
        self.assertSequenceEqual(
            actions,
            ["Zerind",
             "Oradea",
             "Sibiu",
             "Rimnicu Vilcea",
             "Pitesti",
             "Bucharest"]
        )

    def test_romania_bfs(self) -> None:
        """testing search across Romania using BFS"""

        t = create_search_task(
            self.initial_state,
            in_bucharest,
            navigate_romania,
            Queue,
            # debug=True
        )
        t.run_until_done()

        self.assertTrue(t.state.done)

        final: str = cast(str, t.state.final_state)
        self.assertEqual(final, "Bucharest")

        dist: int = cast(int, t.state.path_cost)
        self.assertEqual(dist, 450)

        explored: int = len(t.state.explored)
        self.assertEqual(explored, 8)

        self.assertFalse(t.state.frontier.empty)

        actions: Sequence[str] = cast(
            Sequence[str],
            t.state.action_path
        )
        self.assertSequenceEqual(
            actions,
            ["Sibiu",
             "Fagaras",
             "Bucharest"]
        )

    def test_romania_ucs(self) -> None:
        """testing search across Romania using UCS"""

        t = create_search_task(
            self.initial_state,
            in_bucharest,
            navigate_romania,
            PriorityQueue,
            # debug=True
        )
        t.run_until_done()

        self.assertTrue(t.state.done)

        final: str = cast(str, t.state.final_state)
        self.assertEqual(final, "Bucharest")

        dist: int = cast(int, t.state.path_cost)
        self.assertEqual(dist, 418)

        explored: int = len(t.state.explored)
        self.assertEqual(explored, 12)

        self.assertFalse(t.state.frontier.empty)

        actions: Sequence[str] = cast(
            Sequence[str],
            t.state.action_path
        )
        self.assertSequenceEqual(
            actions,
            ["Sibiu",
             "Rimnicu Vilcea",
             "Pitesti",
             "Bucharest"]
        )

    def test_romania_astar(self) -> None:
        """testing search across Romania using A*"""

        t = create_search_task(
            self.initial_state,
            in_bucharest,
            navigate_romania,
            lambda: PriorityQueue(straight_line_to_bucharest),
            # debug=True
        )
        t.run_until_done()

        self.assertTrue(t.state.done)

        final: str = cast(str, t.state.final_state)
        self.assertEqual(final, "Bucharest")

        dist: int = cast(int, t.state.path_cost)
        self.assertEqual(dist, 418)

        explored: int = len(t.state.explored)
        self.assertEqual(explored, 5)

        self.assertFalse(t.state.frontier.empty)

        actions: Sequence[str] = cast(
            Sequence[str],
            t.state.action_path
        )
        self.assertSequenceEqual(
            actions,
            ["Sibiu",
             "Rimnicu Vilcea",
             "Pitesti",
             "Bucharest"]
        )
