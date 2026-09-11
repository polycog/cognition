# Knowledge Representation Module

## Agentic AI Equivalent and Functional Role
While the agentic AI domain currently lacks a unified consensus and primarily provides loose guidance on organizing context or skills, the `cognition` library uses a specialized data structure called `WorldGraph` to implement the functional equivalent of an agent's **World Model**.

`WorldGraph` serves as the primary state-management layer and the single source of truth for world knowledge, converting raw contextual inputs and skill executions into an organized, and persistent environment state.

## Knowledge Graphs, WorldGraph, and the Decision Process
A **Knowledge Graph (KG)** is a knowledge base that utilizes a graph-structured topology to represent, query, and operate on data. In `cognition`, complex agents represent world state using a `WorldGraph`, which relates a collection of **`Entity`** objects (nodes) via **`BinaryRelation`** objects (edges).

In an agentic decision process, `WorldGraph` serves as the substrate for building and maintaining the agent's internal model of its physical and conceptual environment. By tracking how entities relate to one another and evolve over time, the decision process leverages `WorldGraph` and immutable state snapshots to:

1. **Observe**: Query current topology or derive an immutable `WorldSnapshot` to inspect world state without side effects.
2. **Evaluate**: Perform deterministic evaluations, caching, or state comparison using hashable snapshots.
3. **Execute & Update**: Mutate the central `WorldGraph` following action execution to keep internal state synchronized with external reality.

## Scientific Principles
Knowledge representation sits at the frontier of modern AI and agentic research, building upon classic paradigms of structured knowledge organization. It applies the same core semantic principles that power web-scale systems such as Wikipedia, Google's Knowledge Graph, and WolframAlpha.

* **Primary Reference:** For theoretical foundations on graph-structured knowledge bases, see the [Stanford CS520 Notes on Knowledge Graphs](https://web.stanford.edu/class/cs520/2020/notes/What_is_a_Knowledge_Graph.html).

## Why Use Knowledge Representation?
* **Single Source of Truth:** A central `WorldGraph` instance acts as the authoritative state repository across all agent operations.
* **Stable Contextual Foundation:** Creates a persistent, structured internal model of the agent’s actual environment.
* **LLM Grounding:** Provides a fixed, deterministic reality around which non-deterministic Large Language Model (LLM) inference can be centered, mitigating context drift and hallucinations.
* **Hashable State Snapshots:** The `WorldSnapshot` class provides read-only, hashable access to frozen fact sets, ideal for state hashing, caching, and comparison.
* **Inspectability & Mutability:** Allows programmatic inspection and real-time state mutation so the agent can explicitly reason about upcoming actions or project downstream consequences.

## Implementation Details

All knowledge representation models in `cognition` are built on [Pydantic](https://pydantic.dev/docs/validation/) data models to ensure strict data validation and type safety. Access to the knowledge graph is strictly mediated through these models.

### Core Data Models & Classes

| Class / Primitive | Type / Role | Description | Core Requirements |
| :--- | :--- | :--- | :--- |
| **`WorldGraph`** | Graph Structure | The central, mutable container representing world knowledge; acts as the single source of truth. | Mediates all graph queries and mutation operations through Pydantic schemas. |
| **`Entity`** | Node (Pydantic Model) | Represents distinct objects, physical spaces, or abstract concepts within the world. | **Unique Identifier:** Requires a unique name/ID at instantiation to guarantee identity resolution across the graph. |
| **`BinaryRelation`** | Edge (Pydantic Model) | Directed connections defined over `Entity` pairs that bind nodes into a structured network. | **Context Encoding:** Captures specific spatial, hierarchical, or operational relations between entities. |
| **`WorldSnapshot`** | Immutable Wrapper | Wraps a frozen set of facts derived from a `WorldGraph`. | **Read-Only & Hashable:** Enables side-effect-free reading, caching, and state comparisons. |

### System Operations

```text
[ Entity: Node A ] ---> ( BinaryRelation: Edge ) ---> [ Entity: Node B ]
                               |
                   (Captured in WorldGraph)
                               |
                  v-------------------------v
                  |  WorldSnapshot (Frozen) |
                  ^-------------------------^
```

1. **Instantiation & Validation:** Node creation enforces unique entity identifiers via Pydantic validation before being committed to `WorldGraph`.
2. **Relationship Binding:** `BinaryRelation` objects specify directed relationships between `Entity` pairs (e.g., `located_within` [spatial], `is_a` [hierarchical], `executes_after` [operational]).
3. **Graph Mutation:** Read/write access on `WorldGraph` updates the underlying state in real time as actions are executed.
4. **Snapshot Generation:** When read-only or hashable state access is needed (e.g., for decision verification or caching), `WorldGraph` interacts fluidly with `WorldSnapshot` to wrap a frozen set of facts.
