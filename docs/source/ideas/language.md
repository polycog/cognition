# Language

> **Agentic AI Equivalent**.
> In agentic patterns, structured outputs serve as the interface for tool calling, for formatting parameters whenever the LLM invokes a specific programmatic method. The `language` module builds upon the structured output mechanisms, but restricts them strictly to *transduction* (mapping between natural language and typed domain contracts) without granting the LLM authority to execute tool calls or direct system flow.

## What is `language`, `cognition`'s semantic transducer?
Modern LLM inference engines provide native **structured output** primitives such as JSON mode that forces models into generating schema-compliant JSON payloads. `language` builds upon these mechanisms into a dedicated agent design pattern:

* **From Raw Schemas to Domain Contracts:** Standard structured outputs operate at the JSON Schema level. `cognition` leverages Pydantic and type reflection to map raw language directly to strongly typed Python domain objects that are immediately ready for downstream agentic decision making and reasoning.
* **Bidirectional Transduction:** While native structured outputs are unidirectional (parsing text into key-value pairs), `cognition` treats structured data as a first-class citizen in both directions—pairing deserialization tools with natural-language rendering engines.
* **Isolating Translation from Control Flow:** In agentic designs, structured outputs are invoked inside reasoning loops to format parameters for tool calls. `cognition` repurposes structured outputs as a firewall, ensuring the LLM translates human intent into a static contract before immediately handing control off to deterministic code.

## What are the scientific principles?
LLM-based semantic transduction relies fundamentally on the Distributional Hypothesis, which posits that linguistic elements with shared contextual distributions inhabit adjacent regions within a high-dimensional continuous vector space $\mathbb{R}^d$. Through multi-head self-attention mechanisms, large language models project both high-variance natural prose (e.g., *"cancel my plan immediately"*) and rigid, typed domain contracts (e.g., `{"action": "TERMINATE"}`) onto aligned continuous manifolds within this shared space. By establishing a topological isomorphism between human language and structured schema primitives, the model abstracts away superficial syntactic differences, enabling reliable, invariant bidirectional translation based on contextual meaning.

```{seealso} Further Reading & References
* **[PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding](https://aclanthology.org/2021.emnlp-main.779)** (*Scholak et al., EMNLP 2021*)
  Introduces incremental parsing to constrain language model decoders by assigning $-\infty$ logits to non-conforming tokens at each decoding step.
* **[Synchromesh: Reliable Code Generation from Pre-trained LMs](https://arxiv.org/abs/2201.11227)** (*Poesia et al., ICLR 2022*)
  Combines context-free grammars with stateful completion engines to guarantee both output syntax and contextual type safety.
* **[Pydantic Is All You Need](https://www.youtube.com/watch?v=yj-wSRJwrrc)** (*Jason Liu, AI Engineer Summit*)
  Explores why strongly typed data contracts, rather than unstructured text prompts, serve as the foundational interface for modern AI architecture.
* **[Structured Outputs from LLMs](https://www.youtube.com/watch?v=xpvFinvqRCA)** (*Efficient NLP*)
  A technical deep-dive into the state machines, logit-masking, and token-level constraints powering structured decoding.
```
## Why use the `language` module?
Building reliable AI systems requires separating flexible semantic understanding from core decision making and reasoning. The `language` module serves as an isolating boundary, enabling agent designers to harness the natural language comprehension of LLMs without surrendering system control flow to non-deterministic execution loops.

* **Guaranteed Execution Determinism:** Restricts the LLM strictly to intent translation, ensuring all downstream state transitions and business rules are evaluated by predictable application code.
* **Type-Driven Semantic Parsing:** Uses standard Pydantic models and `DocEnum` metadata to automatically convert unstructured speech into strongly typed, schema-validated domain contracts.
* **Isolated Testability:** Decouples natural language parsing from business logic, allowing core domain rules to be fully unit-tested in traditional CI/CD pipelines without making model calls.
* **Fail-Fast Boundary Security:** Intercepts malformed inputs, missing fields, or invalid domain concepts at the edge before any internal application state can be mutated.
* **Bidirectional Transduction:** Provides symmetric out-of-the-box utilities for both deserializing human speech into domain objects and serializing complex application facts back into natural language.

## Implementation Details
`cognition` provides multiple utilities to integrate language processing & generation within cogent decision-making.
To support access to multiple providers, and integrate with knowledge-driven data modeling, this functionality is built on [Pydantic AI](https://pydantic.dev/docs/ai/).

:::{tip}
A lot of the functionality below builds on description of data, including typing and comments -- to assist, the library includes a `DocEnum` type to provide individualized docstrings for enumerated types (and `AutoDocEnum` for automatically generated values).
:::

* Language production
  * The `describe_facts` function produces a short natural-language description of a collection of data instances.
  * The `FactDescriber` class provides re-usable functionality for instances of a single type.

* Language interpretation
  * The `EnumClassifier` class selects an enumerated value in response to a user utterance.
  * The `ModelPopulator` class attempts to provide a fully instantiated data model based in response to a user utterance.
