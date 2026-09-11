# Cognitive Agent (Cogent)

A `Cogent` (short for **Cog**nitive Ag**ent**) is an integrated runtime framework designed to drive autonomous decision-making by coupling neuro-symbolic reasoning with environment interaction.

> Agentic AI Equivalent
> **Where does this fit in the Agentic AI tech stack?**
> In modern Agentic AI design patterns, a `Cogent` acts as the **Harness / Agent Runtime**. It connects directly with the external environment, manages input/output (I/O) routing, and orchestrates the core execution loop controlling the agent's intelligence operations. (See the [Databricks AI Harness architecture](https://www.databricks.com/blog/ai-harness) for conceptual reference).

---

## What is a Cogent?

At its core, a `Cogent` is a computational entity that continuously executes a three-phase loop:

* **Perceive:** Gathers real-time telemetry and state updates from the environment through **Sensors**.
* **Decide:** Processes incoming information through reasoners to evaluate subproblems and select the next action.
* **Act:** Executes changes back onto the external environment through **Actuators**.

### Neuro-Symbolic Operation
Rather than relying exclusively on Large Language Models (LLMs) to handle all reasoning steps, a `Cogent` relies on neural and symbolic AI components:

* **Natural Language Understanding & Generation:** Handled via Language Models.
* **Situation Understanding:** Resolved through Graph Reasoning.
* **Plan Generation:** Computed via Automated Planning algorithms.
* **Orchestration:** Managed by a Knowledge-Aware Decision Process (**KADP**), which dynamically invokes the appropriate reasoners for the task at hand.

---

## Scientific Principles

The architecture of `Cogent` is grounded in foundational Artificial Intelligence principles, specifically the **Intelligent Agent** paradigm detailed in Russell & Norvig's [*Artificial Intelligence: A Modern Approach* (Chapter 2)](https://people.eecs.berkeley.edu/~russell/aima1e/chapter02.pdf):

* **PEAS Model (Performance, Environment, Actuators, Sensors):** Maintains strict separation between environment interface components (sensors/actuators) and the internal decision cycle.
* **Neuro-Symbolic AI:** Blends statistical probabilistic models (LLMs) with formal, deterministic logic engines (automated planners, graph algorithms) to bound agent behavior with explicit domain constraints.

---

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
