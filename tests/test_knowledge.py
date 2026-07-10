"""
Tests for knowledge code
"""

import unittest

from networkx import NetworkXError

from cognition import BinaryRelation, Entity, WorldGraph

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

    def test_graph(self) -> None:
        """Tests for graph"""

        wg = WorldGraph()

        self.assertEqual(len(list(wg.entities)), 0)
        self.assertEqual(len(list(wg.relations)), 0)

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

        wg.remove_edge(self.r1.entity1.name, self.r1.entity2.name, self.r1.type)

        self.assertSetEqual(set(wg.entities), {self.f1, self.f2})
        self.assertSetEqual(set(wg.relations), {self.r2})

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

        with self.assertRaises(NetworkXError):
            wg.remove_node(self.f1.name)
