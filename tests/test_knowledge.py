"""
Tests for knowledge code
"""

import unittest
import warnings
from typing import cast

from networkx import NetworkXError
from pydantic import ConfigDict, Field, ValidationError

from cognition import (
    BaseSchema,
    BinaryRelation,
    Entity,
    Thawable,
    WorldGraph,
    WorldSnapshot,
)

# ===


class Fact1(Entity):
    """Test entity (sans custom fields)"""

    model_config = ConfigDict(extra="allow")


class Fact2(Entity):
    """Test entity (with custom fields)"""

    a1: int
    a2: str


class Fact3(Entity):
    """Test entity (with mutable custom fields)"""

    a1: list[int]
    a2: set[int]
    a3: dict[str, str]

    def freeze_a3(self) -> str:
        """example custom freezing"""

        return ", ".join(f"{k}={v}" for k, v in self.a3.items())


class Relation1(BinaryRelation):
    """Test relation (sans custom fields)"""

    entity1: Fact1 = Field(frozen=True)
    entity2: Fact1 = Field(frozen=True)


class Relation2(BinaryRelation):
    """Test relation (with custom fields)"""

    entity1: Fact2 = Field(frozen=True)
    entity2: Fact1 = Field(frozen=True)
    ra1: str
    ra2: int


class TestSchema(unittest.TestCase):
    """Tests for knowledge representation code"""

    def test_replace(self) -> None:
        """confirming replace"""

        f2_name = "f2"
        f2_a1 = 42
        f2_a2 = "howdy"

        f2 = Fact2(name=f2_name, a1=f2_a1, a2=f2_a2)
        ff2 = f2.freeze()

        self.assertEqual(f2, cast(Thawable[Fact2], ff2).thaw())

        with self.assertRaises(ValidationError):
            ff2.a1 += 1

        f2.a1 += 1

        self.assertNotEqual(f2.a1, ff2.a1)
        self.assertNotEqual(f2, cast(Thawable[Fact2], ff2).thaw())

        new_ff2 = ff2.replace(a1=f2.a1)

        self.assertEqual(f2.a1, new_ff2.a1)
        self.assertEqual(f2, cast(Thawable[Fact2], new_ff2).thaw())

        with self.assertRaises(KeyError):
            ff2.replace(name="cannot do")

        with self.assertRaises(KeyError):
            ff2.replace(weird="where did this come from")

        with self.assertRaises(ValidationError), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ff2.replace(a1="type mismatch")

    # pylint: disable=too-many-locals
    def test_freeze(self) -> None:
        """confirming freezing"""

        f1_name = "f1"
        other = [1, 2, 3]
        f1 = Fact1(name=f1_name, other=other)  # type: ignore
        self.assertEqual(f1.name, f1_name)
        self.assertEqual(f1.other, other)  # type: ignore
        self.assertEqual(f1.type, "Fact1")

        ff1 = f1.freeze()
        self.assertEqual(ff1.type, "FrozenFact1")
        self.assertEqual(ff1.name, f1_name)
        self.assertEqual(ff1.other, tuple(other))  # type: ignore

        ff1_t = cast(Thawable[Fact1], ff1)
        t1 = ff1_t.thaw()

        self.assertEqual(f1, t1)
        self.assertIsNot(f1, t1)

        # ===

        f2_name = "f2"
        f2_a1 = 42
        f2_a2 = "howdy"
        f2 = Fact2(name=f2_name, a1=f2_a1, a2=f2_a2)
        ff2 = f2.freeze()

        self.assertEqual(ff2.type, "FrozenFact2")
        self.assertEqual(f2.name, ff2.name)
        self.assertEqual(f2.a1, ff2.a1)
        self.assertEqual(f2.a2, ff2.a2)

        self.assertEqual(f2, cast(Thawable[Fact2], ff2).thaw())

        # ==

        f3_name = "f3"
        f3_a1 = [3, 1, 4]
        f3_a2 = {2, 3, 5, 7}
        f3_a3 = {"a": "apple", "b": "banana"}
        f3 = Fact3(name=f3_name, a1=f3_a1, a2=f3_a2, a3=f3_a3)

        self.assertEqual(f3.name, f3_name)
        self.assertEqual(f3.a1, f3_a1)
        self.assertEqual(f3.a2, f3_a2)
        self.assertEqual(f3.a3, f3_a3)

        ff3 = f3.freeze()

        self.assertEqual(ff3.type, "FrozenFact3")
        self.assertEqual(ff3.name, f3_name)
        self.assertEqual(ff3.a1, tuple(f3_a1))
        self.assertEqual(ff3.a2, frozenset(f3_a2))
        self.assertEqual(ff3.a3, "a=apple, b=banana")

        self.assertEqual(f3, cast(Thawable[Fact3], ff3).thaw())

        # ===

        r1 = Relation1(entity1=f1, entity2=f1)
        self.assertIs(r1.entity1, f1)
        self.assertIs(r1.entity2, f1)

        fr1 = r1.freeze()

        self.assertEqual(fr1.type, "FrozenRelation1")
        self.assertEqual(fr1.entity1, f1.freeze())
        self.assertEqual(fr1.entity2, f1.freeze())

        self.assertEqual(r1, cast(Thawable[Relation1], fr1).thaw())

    def test_bad(self) -> None:
        """catching bad schemas"""

        with self.assertRaises(TypeError):

            class _OtherSchema(BaseSchema):
                stuff: int = Field(frozen=True)

                @classmethod
                def fixed_field_names(cls) -> tuple[str, ...]:
                    return (
                        "stuff",
                        "things",
                    )

        with self.assertRaises(TypeError):

            class _BadEntity(Entity):
                name: str
                age: int

        with self.assertRaises(TypeError):

            class _BadRelation(BinaryRelation):
                entity1: Fact1
                entity2: Fact2 = Field(frozen=True)


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-statements
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

        # ===

        self.all_entities = (self.f1, self.f2)
        self.all_relations = (self.r1, self.r2)
        self.all_facts = self.all_entities + self.all_relations

        # ===

        self.ff1 = self.f1.freeze()
        self.ff2 = self.f2.freeze()
        self.fr1 = self.r1.freeze()
        self.fr2 = self.r2.freeze()

        self.frozen_entities = (self.ff1, self.ff2)
        self.frozen_relations = (self.fr1, self.fr2)
        self.frozen_all = self.frozen_entities + self.frozen_relations

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

        # ===

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
            # pylint: disable=comparison-with-itself
            # ruff: ignore[PLR0124]
            snap_empty
            < snap_empty
        )
        self.assertTrue(snap_empty != "foo")

        with self.assertRaises(TypeError):
            self.assertLess(snap_empty, 42)

        with self.assertRaises(TypeError):
            self.assertLessEqual(snap_empty, 3.14)

        self.assertListEqual(list(snap_empty), [])

        with self.assertRaises(ValueError):
            snap_empty.find_first(Entity)

        # ===

        snap_all = WorldSnapshot.click(*self.all_facts)

        self.assertEqual(str(snap_all), "\n".join(str(f) for f in self.frozen_all))
        self.assertEqual(len(snap_all), 4)

        for f in self.all_facts:
            self.assertTrue(f in snap_all)

        self.assertEqual(snap_all, snap_all)
        self.assertNotEqual(snap_empty, snap_all)
        self.assertLess(snap_empty, snap_all)
        self.assertLessEqual(snap_empty, snap_all)
        self.assertLessEqual(WorldSnapshot.click(self.f1), snap_all)

        self.assertSetEqual(set(self.frozen_all), set(snap_all))
        self.assertSetEqual(
            set(self.frozen_all), set(snap_all.by((Entity, BinaryRelation)))
        )
        self.assertSetEqual(set(self.frozen_entities), set(snap_all.by(Entity)))
        self.assertSetEqual(
            set(self.frozen_relations), set(snap_all.by(BinaryRelation))
        )

        self.assertEqual(
            self.f1,
            cast(Thawable[Fact1], snap_all.entity_by_name(self.f1.name)).thaw(),
        )

        self.assertIsNone(snap_all.entity_by_name("--BADBADNAMENAME++"))

        self.assertSetEqual(
            set(snap_all.filter_relations()), set(self.frozen_relations)
        )
        self.assertSetEqual(
            set(
                snap_all.filter_relations(
                    cls_t=cast(type[BinaryRelation], (Relation1 | Relation2))
                )
            ),
            set(self.frozen_relations),
        )

        self.assertSetEqual(set(snap_all.filter_relations(cls_t=Relation1)), {self.fr1})
        self.assertSetEqual(
            set(snap_all.filter_relations(e2=self.ff1)), set(self.frozen_relations)
        )
        self.assertSetEqual(
            set(snap_all.filter_relations(cls_t=Relation2, e1=self.ff2, e2=self.ff1)),
            {self.fr2},
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

        with self.assertRaises(KeyError):
            wg.add_relation(self.r1)

        with self.assertRaises(KeyError):
            wg.get_entity(self.f1.name)

        self.assertEqual(len(list(wg.entities)), 0)
        self.assertEqual(len(list(wg.relations)), 0)

        lf1 = wg.add_entity(self.f1)
        lf2 = wg.add_entity(self.f2)

        self.assertEqual(wg.get_entity(self.f1.name, linked=False), self.f1)
        self.assertEqual(wg.get_entity(self.f2.name).e, self.f2)

        lf2.e.a1 += 1
        self.assertNotEqual(wg.get_entity(self.f2.name).e, self.f2)
        lf2.update()
        self.assertEqual(wg.get_entity(self.f2.name).e, self.f2)
        lf2.e.a1 -= 1
        lf2.update()
        self.assertEqual(wg.get_entity(self.f2.name).e, self.f2)

        self.assertEqual(
            WorldSnapshot.click(*wg.entities), WorldSnapshot.click(self.f1, self.f2)
        )
        self.assertEqual(len(list(wg.relations)), 0)
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f1, self.f2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(KeyError):
            wg.get_relation(
                self.r1.entity1.name,  # pylint: disable=no-member
                self.r1.entity2.name,  # pylint: disable=no-member
                self.r1.type,
            )

        lr1 = wg.add_relation(self.r1)
        lr2 = wg.add_relation(self.r2)

        self.assertEqual(
            # pylint: disable=no-member
            wg.get_relation(self.r1.entity1.name, self.r1.entity2.name, self.r1.type).r,
            self.r1,
        )

        self.assertEqual(
            # pylint: disable=no-member
            wg.get_relation(
                self.r2.entity1.name, self.r2.entity2.name, self.r2.type, linked=False
            ),
            self.r2,
        )

        lr2.r.ra2 += 1
        self.assertNotEqual(
            # pylint: disable=no-member
            wg.get_relation(
                self.r2.entity1.name, self.r2.entity2.name, self.r2.type, linked=False
            ),
            self.r2,
        )
        lr2.update()
        self.assertEqual(
            # pylint: disable=no-member
            wg.get_relation(
                self.r2.entity1.name, self.r2.entity2.name, self.r2.type, linked=False
            ),
            self.r2,
        )
        lr2.r.ra2 -= 1
        lr2.update()
        self.assertEqual(
            # pylint: disable=no-member
            wg.get_relation(
                self.r2.entity1.name, self.r2.entity2.name, self.r2.type, linked=False
            ),
            self.r2,
        )

        self.assertEqual(
            WorldSnapshot.click(*wg.entities), WorldSnapshot.click(self.f1, self.f2)
        )
        self.assertEqual(
            WorldSnapshot.click(*wg.relations), WorldSnapshot.click(self.r1, self.r2)
        )
        self.assertEqual(
            wg.snapshot, WorldSnapshot.click(self.f1, self.f2, self.r1, self.r2)
        )
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        lr1.remove()

        self.assertEqual(
            WorldSnapshot.click(*wg.entities), WorldSnapshot.click(self.f1, self.f2)
        )
        self.assertEqual(
            WorldSnapshot.click(*wg.relations), WorldSnapshot.click(self.r2)
        )
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f1, self.f2, self.r2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(NetworkXError):
            lr1.remove()

        oe_linked = list(lf2.outgoing)

        self.assertEqual(len(oe_linked), 1)
        self.assertEqual(oe_linked[0].r, self.r2)

        oe = list(wg.outgoing_relations(self.f2, linked=False))

        self.assertEqual(len(oe), 1)
        self.assertEqual(oe[0], self.r2)

        lf1.remove()

        self.assertEqual(
            WorldSnapshot.click(*wg.entities), WorldSnapshot.click(self.f2)
        )
        self.assertEqual(len(list(wg.relations)), 0)
        self.assertEqual(wg.snapshot, WorldSnapshot.click(self.f2))
        self.assertEqual(wg.snapshot, WorldGraph.from_snapshot(wg.snapshot).snapshot)

        with self.assertRaises(NetworkXError):
            lf1.remove()
