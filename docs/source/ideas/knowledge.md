# Knowledge Representation & Organization

Complex agents can represent state as a `WorldGraph`, which relates a collection of `Entity` objects (i.e., nodes) via `BinaryRelation` objects (i.e., edges).
These representations are built on [Pydantic](https://pydantic.dev/docs/validation/) data models.
A `WorldGraph` instance is intended to be a single source of truth, with access mediated through the above data models.

To support read-only, hashable access to the above data, the `WorldGraph` interacts fluidly with a `WorldSnapshot` class, which wraps a frozen set of the facts that make up a class.
