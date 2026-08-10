"""
Knowledge organization
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import singledispatchmethod
from itertools import chain
from typing import Any, Self, cast

import networkx as nx

from ..util.functypes import Predicate
from .representation import BinaryRelation, Entity, Fact

# ===

_logger = logging.getLogger(__name__)

# ===

type _ClassInfo[T] = type[T] | tuple["_ClassInfo[T]", ...]
"""allows for isinstance multi-types"""


@dataclass(frozen=True)
class WorldSnapshot:
    """
    A fixed set of entities and/or relations
    """

    items: frozenset[Fact]
    """Fixed set of facts"""

    # ===

    def __str__(self) -> str:
        """
        :return: facts in ascending order
        """

        return "\n".join(str(f) for f in sorted(self.items, key=str))

    def __len__(self) -> int:
        """
        :return: number of facts
        """

        return len(self.items)

    def __contains__(self, item: Fact) -> bool:
        """
        :param item: fact of interest
        :return: ``True`` if supplied fact is in this set
        """
        return item in self.items

    def __eq__(self, other: object) -> bool:
        """
        :param other: some object
        :return: ``True`` if the object is of this type and has the same facts
        """

        if not isinstance(other, WorldSnapshot):
            return NotImplemented

        return self.items == other.items

    def __lt__(self, other: object) -> bool:
        """
        :param other: some object
        :return: ``True`` if the object is of this type and has a strict subset of the facts
        """

        if not isinstance(other, WorldSnapshot):
            return NotImplemented

        return self.items < other.items

    def __le__(self, other: object) -> bool:
        """
        :param other: some object
        :return: ``True`` if the object is of this type and has a subset of the facts
        """

        if not isinstance(other, WorldSnapshot):
            return NotImplemented

        return self.items <= other.items

    def __iter__(self) -> Iterator[Fact]:
        """
        :return: iterator over the facts
        """

        yield from self.items

    @classmethod
    def click(cls, *facts: Fact) -> Self:
        """
        Convenience method for producing
        a snapshot from a supplied source

        :param facts: source of facts
        :return: resulting snapshot
        """

        return cls(frozenset(facts))

    def copy(self, add: Iterable[Fact] = (), remove: Iterable[Fact] = ()) -> Self:
        """
        Convenience method for producing
        a new snapshot from the contents
        of this snapshot + some added facts
        - some removed facts.

        :param add: fact(s) to add
        :param remove: fact(s) to remove
        :return: resulting snapshot
        """

        return self.click(*(self.items - set(remove) | set(add)))

    def by[FT](self, cls_t: _ClassInfo[FT]) -> Iterable[FT]:
        """
        Access by fact type

        :param cls_t: filter type
        :return: facts matching the filter
        """

        return tuple(item for item in self.items if isinstance(item, cls_t))

    def find_first[FT](
        self, cls_t: type[FT], check: Predicate[FT] = lambda _: True
    ) -> FT:
        """
        Finds the first typed fact that satisfies the check

        :param cls_t: filter type
        :param check: return gate
        :return: first found fact
        :raises ValueError: no fact of the supplied type satisfies the check
        """

        for item in self.by(cls_t):
            if check(item):
                return item

        raise ValueError("Could not find a satisfying fact")

    def entity_by_name(self, entity_name: str) -> Entity | None:
        """
        Finds the first entity with the supplied name

        :param entity_name: target name
        :return: entity, or ``None`` if unused name
        """

        try:
            return self.find_first(Entity, lambda e: e.name == entity_name)
        except ValueError:
            return None

    def filter_relations[RT: BinaryRelation](
        self,
        cls_t: type[RT] | None = None,
        e1: Entity | None = None,
        e2: Entity | None = None,
    ) -> Iterable[BinaryRelation]:
        """
        Finds all relation(s) that match the supplied criteria

        :param cls_t: relation type criterion (or ``None`` for unconstrained)
        :param e1: first entity (or ``None`` for unconstrained)
        :param e2: second entity (or ``None`` for unconstrained)
        :return: any matching relations
        """

        def _p(r: BinaryRelation) -> bool:
            return all(
                (
                    True if e1 is None else r.entity1 == e1,
                    True if e2 is None else r.entity2 == e2,
                )
            )

        yield from (
            r for r in self.by(cls_t if cls_t is not None else BinaryRelation) if _p(r)
        )


class WorldGraph:
    """
    Graph of binary relations (edges) between entities (nodes)
    """

    _TYPE_ATTR = "_type"
    """Internal attribute for storing typing data"""

    _FIELDS_ATTR = "_fields"
    """Internal attribute for storing field data"""

    g: nx.MultiDiGraph[str]
    """
    Knowledge graph - publicly exposed,
    but should be handled in a read-only
    fashion and conversion data read/writes
    left to the :class:`WorldGraph` API
    """

    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

        _logger.info("Initialized an empty %s", type(self).__name__)

    @singledispatchmethod
    def add(self, data: Fact) -> Self:
        """
        Base method for adding graph data.

        This method is only invoked if called with improper data.

        :param data: item to add
        :return: reference to this graph
        :raises NotImplementedError: bad type
        """

        raise NotImplementedError("Unsupported type")

    @add.register
    def _(self, data: Entity) -> Self:
        """
        Convenience redirect to :meth:`WorldGraph.add_entity`

        :param data: entity to add
        :return: reference to this graph
        """

        return self.add_entity(data)

    @add.register
    def _(self, data: BinaryRelation) -> Self:
        """
        Convenience redirect to :meth:`WorldGraph.add_relation`

        :param data: relation to add
        :return: reference to this graph
        """

        return self.add_relation(data)

    def add_entity(self, e: Entity) -> Self:
        """
        Using the entity name as id, sets the associated
        node data within the graph

        :param e: entity with node data
        :return: reference to this graph
        """

        _logger.info("Adding entity to %s", type(self).__name__)
        _logger.debug(e)

        # supports readable dot
        label = str(e)
        cf = list(e.custom_fields)
        if cf:
            label = "\n".join([f"{e.type}({e.name})"] + [f"{k}={v}" for k, v in cf])

        self.g.add_node(
            e.name,
            label=label,
            **{
                WorldGraph._TYPE_ATTR: type(e),
                WorldGraph._FIELDS_ATTR: dict(e.custom_fields),
            },
        )

        return self

    def add_relation(self, r: BinaryRelation) -> Self:
        """
        Using the (entity1 -[key=r.type]-> entity2) as id,
        sets the associated edge data within the graph

        :param r: relation with edge data
        :return: reference to this graph
        :raises KeyError: supplied node not in the graph
        """

        _logger.info("Adding relation to %s", type(self).__name__)
        _logger.debug(r)

        for e in (r.entity1, r.entity2):
            if not self.g.has_node(e.name):
                err = KeyError(f"Unknown node id: {e.name}")

                _logger.error(err)
                raise err

        label = r.type
        cf = list(r.custom_fields)
        if cf:
            label = "\n".join([r.type] + [f"{k}={v}" for k, v in cf])

        self.g.add_edge(
            r.entity1.name,
            r.entity2.name,
            key=r.type,
            label=label,
            **{
                WorldGraph._TYPE_ATTR: type(r),
                WorldGraph._FIELDS_ATTR: dict(r.custom_fields),
            },
        )

        return self

    def get_entity(self, entity_name: str) -> Entity:
        """
        Retrieves an entity given its name

        :param entity_name: node to find
        :return: node data
        :raises KeyError: supplied entity name not in the graph
        """

        _logger.debug("Attempting to find entity named '%s'", entity_name)

        try:
            node = self.g.nodes[entity_name]
        except KeyError:
            _logger.error("Unknown name: %s", entity_name)
            raise

        cls = node[WorldGraph._TYPE_ATTR]

        return cls(name=entity_name, **node[WorldGraph._FIELDS_ATTR])  # type: ignore

    @property
    def entities(self) -> Iterable[Entity]:
        """
        All graph entities

        :return: data from all graph nodes
        """

        yield from (self.get_entity(id) for id in self.g)

    def produce_relation(
        self, entity1: Entity, entity2: Entity, edge_info: dict[str, Any]
    ) -> BinaryRelation:
        """
        Produces a relation given the supplied edge data
        (assumed to be directly from the graph)

        :param entity1: starting entity
        :param entity2: ending entity
        :param edge_info: edge attribute info
        :return: edge data
        """

        cls = edge_info[WorldGraph._TYPE_ATTR]

        return cls(  # type: ignore
            entity1=entity1,
            entity2=entity2,
            **edge_info[WorldGraph._FIELDS_ATTR],
        )

    def get_relation(
        self, entity1_name: str, entity2_name: str, edge_type: str
    ) -> BinaryRelation:
        """
        Retrieves a relation give the names of the
        associated entities and the relation type

        :param entity1_name: starting node name
        :param entity2_name: ending node name
        :param edge_type: edge schema type
        :return: edge data
        :raises KeyError: supplied entity name not in the graph
        """

        _logger.debug(
            "Attempting to find relation: %s -[%s]-> %s",
            entity1_name,
            edge_type,
            entity2_name,
        )

        try:
            return self.produce_relation(
                self.get_entity(entity1_name),
                self.get_entity(entity2_name),
                self.g[entity1_name][entity2_name][edge_type],
            )
        except KeyError as e:
            _logger.error("Unknown entity/edge related to key: %s", e)
            raise

    @property
    def relations(self) -> Iterable[BinaryRelation]:
        """
        All graph relations

        :return: data from all graph edges
        """

        yield from (
            self.produce_relation(self.get_entity(u), self.get_entity(v), d)
            for u, v, d in self.g.edges(data=True)
        )

    @property
    def snapshot(self) -> WorldSnapshot:
        """
        Produces a snapshot of this graph

        :return: static snapshot of all entities and relations
        """

        return WorldSnapshot.click(
            *cast(Iterable[Fact], chain(self.entities, self.relations))
        )

    @classmethod
    def from_snapshot(cls, snap: WorldSnapshot) -> Self:
        """
        Create a graph from a snapshot

        :param snap: set of entities/relations
        :return: resulting graph
        """

        wg = cls()
        for e in snap.by(Entity):
            wg.add_entity(e)

        for r in snap.by(BinaryRelation):
            wg.add_relation(r)

        return wg

    def remove_node(self, entity_name: str) -> Self:
        """
        Removes a graph node

        :param entity_name: node name to remove
        :return: reference to this graph
        """

        _logger.info(
            "Attempting to remove node from %s",
            type(self).__name__,
        )
        _logger.debug(
            "Entity name: %s",
            entity_name,
        )

        try:
            self.g.remove_node(entity_name)
        except nx.NetworkXError as e:
            _logger.error(e)
            raise

        return self

    def remove_edge(self, entity1_name: str, entity2_name: str, edge_type: str) -> Self:
        """
        Remove a graph edge

        :param entity1_name: starting node name
        :param entity2_name: ending node name
        :param edge_type: edge schema type
        :return: reference to this graph
        """

        _logger.info(
            "Attempting to remove edge from %s",
            type(self).__name__,
        )
        _logger.debug(
            "Edge: %s -[%s]-> %s",
            entity1_name,
            edge_type,
            entity2_name,
        )

        try:
            self.g.remove_edge(entity1_name, entity2_name, edge_type)
        except nx.NetworkXError as e:
            _logger.error(e)
            raise

        return self
