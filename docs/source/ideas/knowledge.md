# World Graph

```{admonition} Agentic AI Equivalent
:class: note
The agentic AI ecosystem currently lacks a consensus on how agents should manage world state. Most frameworks rely on ad-hoc context construction that bundles transient world state into the prompt window alongside system instructions, tool execution logs, and user inputs.

`cognition` provides `WorldGraph` to maintain a stable, rich internal description of the world, providing a structured foundation for deterministic reasoning, long-horizon planning, and consistent decision-making.
```



## What is a world graph?
While most agentic frameworks rely on unstructured context windows or ad-hoc skill definitions, `cognition` provides a dedicated, persistent state-management layer: the **`WorldGraph`**. It serves as the agent's **World Model**—the single source of truth for its physical and conceptual environment.

### Knowledge Graphs as World Models
A **Knowledge Graph (KG)** is a structured data network that represents information as real-world entities connected by explicit, semantic relationships. Unlike flat text buffers or traditional tables, a knowledge graph makes complex webs of interconnected data directly queryable and machine-readable.

In `cognition`, this graph structure is implemented via `WorldGraph`, built from two core primitives:
* **`Entity` (Nodes):** Represent objects, concepts, actors, or state variables in the environment.
* **`BinaryRelation` (Edges):** Define directed relationships, attributes, and dependencies between entities.

By converting raw contextual inputs and tool outputs into a structured graph, `WorldGraph` prevents context drift and grounds the agent's decision-making process in a coherent, queryable reality.

### The WorldGraph Execution Loop
During runtime, `WorldGraph` provides the substrate for tracking how the environment evolves across three core phases:
1. **Observe:** Query live graph topology directly, or generate an immutable `WorldSnapshot` to inspect state without side effects.
2. **Evaluate:** Perform deterministic state comparisons, differential tracking, or cached evaluations using hashable snapshots.
3. **Execute & Update:** Mutate the central `WorldGraph` following action execution to keep internal state synchronized with external reality.

## What are the scientific principles?
The origins of knowledge graphs trace back to 1960s artificial intelligence research, when pioneers like Ross Quillian introduced [semantic networks](https://onlinelibrary.wiley.com/doi/abs/10.1002/bs.3830120511) and Marvin Minsky proposed [frame systems](https://dspace.mit.edu/entities/publication/0eca0164-cb5f-42de-8c86-43f54b23306d) to model human associative memory through interlinked concepts and explicit relationships. Throughout the 1980s and 1990s, these concepts matured into formal ontologies and [description logics](https://en.wikipedia.org/wiki/Description_logic), establishing mathematical frameworks for machine-driven reasoning. The modern graph ecosystem took shape in the early 2000s with the W3C’s Semantic Web standards, namely RDF and OWL, and collaborative knowledge bases like Metaweb's Freebase. The paradigm achieved widespread industry adoption in 2012 when Google formally introduced its "Knowledge Graph," popularizing the shift from keyword index matching to entity-centric understanding ("things, not strings") and solidifying graph topologies as the foundation for modern semantic context.

```{seealso} Further Reading & References
- **Stanford CS520:** [What is a Knowledge Graph?](https://web.stanford.edu/class/cs520/2020/notes/What_is_a_Knowledge_Graph.html) — Comprehensive lecture notes on theoretical foundations.
- **Google AI Blog:** [Introducing the Knowledge Graph: things, not strings](https://blog.google/products-and-platforms/products/search/introducing-knowledge-graph-things-not/) — Foundational post on web-scale semantic search.
- **Computerphile:** [Semantic Networks & AI Reasoning](https://www.youtube.com/watch?v=PZBm7M0HGzw) — Prof. Elena Simperl breaks down semantic network theory (12 min video).
```


## Why use world graphs?
Knowledge graphs are at the core of modern search and recommendation systems. `cognition` brings this foundational AI concept to the agentic AI ecosystem. Using a world graph to describe the current state of the environment provides several advantages vis-a-vis a 'context'.
* **Single Source of Truth:** A central `WorldGraph` instance acts as the authoritative state repository across all agent operations.
* **Stable Contextual Foundation:** Creates a persistent, structured internal model of the agent’s actual environment.
* **LLM Grounding:** Provides a fixed, deterministic reality around which non-deterministic Large Language Model (LLM) inference can be centered, mitigating context drift and hallucinations.
* **Hashable State Snapshots:** The `WorldSnapshot` class provides read-only, hashable access to frozen fact sets, ideal for state hashing, caching, and comparison.
* **Inspectability & Mutability:** Allows programmatic inspection and real-time state mutation so the agent can explicitly reason about upcoming actions or project downstream consequences.

## Implementation Details
World models in `cognition` are built on [Pydantic](https://pydantic.dev/docs/validation/) data models to ensure strict data validation and type safety. Access to the knowledge graph is strictly mediated through these models. Underneath the hood, `cognition` uses standard Python libraries: [networkx](https://networkx.org/en/), [Neo4j](https://neo4j.com/).

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
