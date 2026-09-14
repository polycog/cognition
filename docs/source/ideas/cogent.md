# Cognitive Agent (Cogent)
> **Agentic AI Equivalent**
> In Agentic AI design patterns, a harness or agent runtime connects directly with the external environment, manages input/output (I/O) routing, and implements the core execution loop controlling the agent's task performance. (See the [Databricks AI Harness architecture](https://www.databricks.com/blog/ai-harness) for conceptual reference). ReACT paradigm

## What is a Cogent?
A `Cogent` (short for **Cog**nitive Ag**ent**) is an integrated runtime framework designed to drive autonomous decision-making by coupling [neurosymbolic](https://en.wikipedia.org/wiki/Neuro-symbolic_AI) foundation with environment interaction. At its core, a `Cogent` continuously executes a three-phase loop:

* **Perceive:** Gathers real-time telemetry from the environment through **Sensors**.
* **Decide:** Processes incoming information through decision processes and reasoners to evaluate subproblems and select the next action.
* **Act:** Executes changes back onto the external environment through **Actuators**.

### Neurosymbolic Operation
Rather than relying exclusively on Large Language Models (LLMs) to handle all reasoning and decision making steps, a `Cogent` relies on a heterogenous reasoning foundation implementing both neural and symbolic AI:

* **Natural Language Understanding & Generation:** Handled via [Language Models](language.md).
* **Situational Awareness:** Resolved through [Knowledge Graph Reasoning](knowledge.md).
* **Orchestration:** Managed by a [Knowledge-Aware Decision Process](kadp.md), which dynamically invokes the appropriate reasoners for the task at hand.
* **Plan Generation:** Computed via Automated [Planning](planning.md) algorithms.

As the `cognition` library grows it will be extended to include algorithms for [causal reasoning](https://pgmpy.org/index.html), [temporal logics](https://github.com/lab-v2/pyreason), [spatio-temporal planning](https://gitlab.com/wmgp9/nyx), diagnosis and remediation, numerical optimization etc.; all centered out processing structured information repesented via a knowledge graph.


## Scientific Principles
The `cogent` component is grounded in classical Intelligent Agent theory, combining probabilistic reasoning with deterministic execution guarantees. Built upon the PEAS (Performance, Environment, Actuators, Sensors) paradigm, it establishes a formal boundary that decouples perception and action interfaces from the internal cognitive decision loop. To achieve adaptive yet reliable agent behavior, `cogent` employs a neurosymbolic foundation that integrates the generative, open-ended capabilities of Large Language Models with formal logic engines, graph algorithms, and automated planners. This hybrid foundation enables flexible language understanding while ensuring system actions remain provably bounded within explicit domain constraints.

The `cogent` component and the broader `cognition` library represent a modern instantiation of the [cognitive architecture](https://en.wikipedia.org/wiki/Cognitive_architecture) movement, particularly [Soar](https://soar.eecs.umich.edu/) for the era of foundation models. Where early symbolic architectures struggled with brittle perception and knowledge-acquisition bottlenecks, modern Large Language Models offer unprecedented semantic flexibility but lack structural statefulness, deliberate goal regulation, and bounded execution loops. `cognition` bridges this historical divide by embedding statistical models within a structured cognitive loop.

```{seealso} Further Reading & References
* **[Artificial Intelligence: A Modern Approach (Chapter 2: Intelligent Agents)](https://aima.cs.berkeley.edu/)** (*Russell & Norvig, Pearson*): Introduces the PEAS framework and formal agent-environment interaction models that underpin `cogent`'s decoupled interface design.
* **[Experts Explain: What is AI?](https://www.youtube.com/watch?v=W5E2K7x5pGo)** (*Stuart Russell, World Economic Forum*): An overview of artificial intelligence and intelligent agent foundations presented by Prof. Stuart Russell.
* **[Ep. 13 - AI Agents to Model Human Cognition](https://www.youtube.com/watch?v=YP2YbF93-1Y)** (*John Laird*): Explores four decades of cognitive architecture research, detailing how unified models like Soar integrate reasoning, memory, and decision-making to build autonomous AI agents.
```


## Why Use a Cogent?
`Cogent` provides an integrated runtime to leverage a broad suite of AI algorithms beyond language models for predictable, verifiable, and autonomous decision-making.

* **Heterogenous Reasoning Capabilities:**
  * **Supported:** Natural Language processing, Graph-based situational awareness, Automated Planning.
  * **Planned Roadmap:** Spatio-temporal planning, constraint satisfaction, numerical optimization, causal reasoning, automated diagnosis, and repair.
* **Enterprise Trust & Safety:** Relying solely on stochastic LLM generation introduces hallucination risks and unexplainable behavior. Utilizing science-backed, general-purpose reasoning machinery enables developers to build inspectable, provably safe autonomous agents.

---

## Implementation Details

A `Cogent` implements its Perceive-Decide-Act loop by integrating three core components:

* A supplied `DecisionProcess` (KADP orchestrator)
* Any number of supplied `Sensor` objects
* Any number of supplied `Actuator` objects

![Decision Process Cycle](../_static/cogent_cycle.png)

:::{note}
Each `Sensor` and `Actuator` must be assigned a unique name. This name corresponds directly to its key path within the `IOContainer`:
* Sensors write to `io.i.<sensor_name>`
* Actuators read from `io.o.<actuator_name>`
:::

:::{tip}
To simplify I/O mapping and reduce path lookup errors:
* A `Sensor` can supply a custom **reader** function to automatically extract and format raw data from the `IOContainer`.
* An `Actuator` can supply a custom **invoker** function to supply output commands directly to the `IOContainer`.
:::
