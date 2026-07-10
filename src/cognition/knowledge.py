"""
Knowledge representation
"""

from __future__ import annotations

from typing import Any, Self

from collections.abc import Iterable

from functools import singledispatchmethod

from pydantic import (
    BaseModel,
    ConfigDict,
)

import networkx as nx

#


class TypedSchema(BaseModel):
    """Provides convenient access to schema type"""

    @property
    def type(self) -> str:
        """
        Access to schema type name

        :return: class name
        """

        return type(self).__name__


class Entity(TypedSchema):
    """
    Distinct object, concept, or event
    that is named and immutable
    """

    model_config = ConfigDict(frozen=True)
    name: str

    def __str__(self) -> str:
        """
        KR representation

        :return: e.type(name='e.name'[, e.field1=value1, ...])
        """

        cf = list(self.custom_fields)

        start = f"{self.type}(name={self.name}"
        if cf:
            return f"{start}, {", ".join(f"{k}={v}" for k,v in self.custom_fields)})"

        return f"{start})"

    @property
    def custom_fields(self) -> Iterable[tuple[str, Any]]:
        """
        Fields other than name

        :return: name/value pairs for non-name fields, if any
        """

        yield from ((k, v) for k, v in self.model_dump().items() if k != "name")


class BinaryRelation(TypedSchema):
    """
    A relationship between two entities
    """

    model_config = ConfigDict(frozen=True)
    entity1: Entity
    entity2: Entity

    def __str__(self) -> str:
        """
        KR representation

        :return: r.type(entity1=r.entity1, entity2=r.entity2[, r.field1=value1, ...])
        """

        cf = list(self.custom_fields)

        start = f"{self.type}(entity1={self.entity1}, entity2={self.entity2}"
        if cf:
            return (
                f"{start}, " f"{", ".join(f"{k}={v}" for k,v in self.custom_fields)})"
            )

        return f"{start})"

    @property
    def custom_fields(self) -> Iterable[tuple[str, Any]]:
        """
        Fields other than name

        :return: name/value pairs for non-name fields, if any
        """

        yield from (
            (k, v)
            for k, v in self.model_dump().items()
            if k not in ("entity1", "entity2")
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
    left to the `WorldGraph` API
    """

    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    @singledispatchmethod
    def add(self, data: Entity | BinaryRelation) -> Self:
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

        for e in (r.entity1, r.entity2):
            if not self.g.has_node(e.name):
                raise KeyError(f"Unknown node id: {e.name}")

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
        """

        node = self.g.nodes[entity_name]
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
        """

        return self.produce_relation(
            self.get_entity(entity1_name),
            self.get_entity(entity2_name),
            self.g[entity1_name][entity2_name][edge_type],
        )

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

    def remove_node(self, entity_name: str) -> Self:
        """
        Removes a graph node

        :param entity_name: node name to remove
        :return: reference to this graph
        """

        self.g.remove_node(entity_name)

        return self

    def remove_edge(self, entity1_name: str, entity2_name: str, edge_type: str) -> Self:
        """
        Remove a graph edge

        :param entity1_name: starting node name
        :param entity2_name: ending node name
        :param edge_type: edge schema type
        :return: reference to this graph
        """

        self.g.remove_edge(entity1_name, entity2_name, edge_type)

        return self
