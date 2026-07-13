"""
Tests for knowledge code
"""

import unittest

from typing import cast

from networkx import NetworkXError

from cognition import BinaryRelation, Entity, WorldGraph, WorldSnapshot

#


class Fact1(Entity):
    """Test entity (sans custom fields)"""


class Fact2(Entity):
    """Test entity (with custom fields)"""

    a1: int
    a2: str


class Relation1(BinaryRelation):
    """Test relation (sans custom fields)"""

    entity1: Fact1
    entity2: Fact1


class Relation2(BinaryRelation):
    """Test relation (with custom fields)"""

    entity1: Fact2
    entity2: Fact1
    ra1: str
    ra2: int


# pylint: disable=too-many-instance-attributes
class TestKnowledge(unittest.TestCase):
    """Tests for knowledge code"""

    def setUp(self) -> None:
        """common data"""

        self.f1_name = "f1"
        self.f1 = Fact1(name=self.f1_name)

        self.f2_name = "f2"
        self.f2_a1 = 42
        self.f2_a2 = "howdy"
        self.f2 = Fact2(name=self.f2_name, a1=self.f2_a1, a2=self.f2_a2)

        self.r1 = Relation1(entity1=self.f1, entity2=self.f1)

        self.r2_ra1 = "anything I can do for you?"
        self.r2_ra2 = 8675309
        self.r2 = Relation2(
            entity1=self.f2, entity2=self.f1, ra1=self.r2_ra1, ra2=self.r2_ra2
        )

        #

        self.all_entities = (self.f1, self.f2)
        self.all_relations = (self.r1, self.r2)
        self.all_facts = self.all_entities + self.all_relations

    def test_entity_relation(self) -> None:
        """Tests for entities and relations"""

        self.assertEqual(self.f1.type, type(self.f1).__name__)
        self.assertEqual(self.f1.name, self.f1_name)
        self.assertEqual(len(list(self.f1.custom_fields)), 0)
        self.assertEqual(str(self.f1), f"Fact1(name={self.f1_name})")

        self.assertEqual(self.f2.type, type(self.f2).__name__)
        self.assertEqual(self.f2.name, self.f2_name)
        self.assertDictEqual(
            dict(self.f2.custom_fields), {"a1": self.f2_a1, "a2": self.f2_a2}
        )
        self.assertEqual(
            str(self.f2),
            f"Fact2(name={self.f2_name}, a1={self.f2_a1}, a2={self.f2_a2})",
        )

        #

        self.assertEqual(self.r1.type, type(self.r1).__name__)
        self.assertEqual(self.r1.entity1, self.f1)
        self.assertEqual(self.r1.entity2, self.f1)
        self.assertEqual(len(list(self.r1.custom_fields)), 0)
        self.assertEqual(
            str(self.r1), f"Relation1(entity1={self.f1}, entity2={self.f1})"
        )

        self.assertEqual(self.r2.type, type(self.r2).__name__)
        self.assertEqual(self.r2.entity1, self.f2)
        self.assertEqual(self.r2.entity2, self.f1)
        self.assertDictEqual(
            dict(self.r2.custom_fields), {"ra1": self.r2_ra1, "ra2": self.r2_ra2}
        )
        self.assertEqual(
            str(self.r2),
            (
                f"Relation2(entity1={self.f2}, "
                f"entity2={self.f1}, "
                f"ra1={self.r2_ra1}, "
                f"ra2={self.r2_ra2})"
            ),
        )

    def test_snapshot(self) -> None:
        """Tests for snapshot"""

        snap_empty = WorldSnapshot.click()

        self.assertEqual(str(snap_empty), "")
        self.assertEqual(len(snap_empty), 0)

        self.assertFalse(self.f1 in snap_empty)
        self.assertFalse(self.f2 in snap_empty)
        self.assertFalse(self.r1 in snap_empty)
        self.assertFalse(self.r2 in snap_empty)

        self.assertEqual(snap_empty, snap_empty)
        self.assertLessEqual(snap_empty, snap_empty)
        self.assertFalse(
            snap_empty < snap_empty  # pylint: disable=comparison-with-itself
        )
        self.assertTrue(snap_empty != "foo")

        with self.assertRaises(TypeError):
            self.assertLess(snap_empty, 42)

        with self.assertRaises(TypeError):
            self.assertLessEqual(snap_empty, 3.14)

        self.assertListEqual(list(snap_empty), [])

        with self.assertRaises(ValueError):
            snap_empty.find_first(Entity)

        #

        snap_all = WorldSnapshot.click(*self.all_facts)

        self.assertEqual(str(snap_all), "\n".join(str(f) for f in self.all_facts))
        self.assertEqual(len(snap_all), 4)

        for f in self.all_facts:
            self.assertTrue(f in snap_all)

        self.assertEqual(snap_all, snap_all)
        self.assertNotEqual(snap_empty, snap_all)
        self.assertLess(snap_empty, snap_all)
        self.assertLessEqual(snap_empty, snap_all)
        self.assertLessEqual(WorldSnapshot.click(self.f1), snap_all)

        self.assertSetEqual(set(self.all_facts), set(snap_all))
        self.assertSetEqual(
            set(self.all_facts), set(snap_all.by(Entity | BinaryRelation))
        )
        self.assertSetEqual(set(self.all_entities), set(snap_all.by(Entity)))
        self.assertSetEqual(set(self.all_relations), set(snap_all.by(BinaryRelation)))

        self.assertEqual(
            self.f1,
            snap_all.entity_by_name(self.f1.name),
        )

        self.assertIsNone(snap_all.entity_by_name("--BADBADNAMENAME++"))

        self.assertSetEqual(set(snap_all.filter_relations()), set(self.all_relations))
        self.assertSetEqual(
            set(
                snap_all.filter_relations(
                    cls_t=cast(type[BinaryRelation], (Relation1 | Relation2))
                )
            ),
            set(self.all_relations),
        )

        self.assertSetEqual(
            set(snap_all.filter_relations(cls_t=Relation1)), set((self.r1,))
        )
        self.assertSetEqual(
            set(snap_all.filter_relations(e2=self.f1)), set(self.all_relations)
        )
        self.assertSetEqual(
            set(snap_all.filter_relations(cls_t=Relation2, e1=self.f2, e2=self.f1)),
            set((self.r2,)),
        )

        self.assertEqual(
            snap_empty.copy(add=self.all_entities),
            snap_all.copy(remove=self.all_relations),
        )
        self.assertEqual(
            snap_all.copy(remove=(self.f1, self.r2), add=(self.r2, self.f1)), snap_all
        )

    def test_graph(self) -> None:
        """Tests for graph"""

        wg = WorldGraph()

        self.assertEqual(len(list(wg.entities)), 0)
        self.assertEqual(len(list(wg.relations)), 0)
        self.assertEqual(wg.snapshot, WorldSnapshot.click())
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(NotImplementedError):
            wg.add("foo")

        with self.assertRaises(KeyError):
            wg.add(self.r1)

        self.assertEqual(len(list(wg.entities)), 0)
        self.assertEqual(len(list(wg.relations)), 0)

        wg.add(self.f1).add(self.f2)

        self.assertEqual(wg.get_entity(self.f1.name), self.f1)
        self.assertEqual(wg.get_entity(self.f2.name), self.f2)

        self.assertSetEqual(set(wg.entities), {self.f1, self.f2})
        self.assertEqual(len(list(wg.relations)), 0)
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f1, self.f2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        wg.add(self.r1).add(self.r2)

        self.assertEqual(
            wg.get_relation(self.r1.entity1.name, self.r1.entity2.name, self.r1.type),
            self.r1,
        )

        self.assertEqual(
            wg.get_relation(self.r2.entity1.name, self.r2.entity2.name, self.r2.type),
            self.r2,
        )

        self.assertSetEqual(set(wg.entities), {self.f1, self.f2})
        self.assertSetEqual(set(wg.relations), {self.r1, self.r2})
        self.assertEqual(
            wg.snapshot, WorldSnapshot.click(self.f1, self.f2, self.r1, self.r2)
        )
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        wg.remove_edge(self.r1.entity1.name, self.r1.entity2.name, self.r1.type)

        self.assertSetEqual(set(wg.entities), {self.f1, self.f2})
        self.assertSetEqual(set(wg.relations), {self.r2})
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f1, self.f2, self.r2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(NetworkXError):
            wg.remove_edge(self.r1.entity1.name, self.r1.entity2.name, self.r1.type)

        oe = list(wg.g.out_edges(self.f2.name, data=True))

        self.assertEqual(len(oe), 1)

        u, v, e_d = oe[0]
        self.assertEqual(
            wg.produce_relation(wg.get_entity(u), wg.get_entity(v), e_d), self.r2
        )

        wg.remove_node(self.f1.name)

        self.assertSetEqual(set(wg.entities), {self.f2})
        self.assertEqual(len(list(wg.relations)), 0)
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(NetworkXError):
            wg.remove_node(self.f1.name)
