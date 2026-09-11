# Planning

The `Planning` module provides algorithms and abstractions for generating valid sequences of actions to transition an agent from an initial state to a target goal.

## Agentic AI Equivalent

* **Concept Equivalent:** **Chain of Thought (CoT) / Deliberative Reasoning**
* **Function Implemented:** Step-by-step reasoning and search over discrete problem spaces.

While Large Language Models (LLMs) perform Chain of Thought via probabilistic next-token prediction, formal planning implements explicit, algorithmic step-by-step reasoning. It systematically decomposes high-level goals into valid action chains by evaluating hypothetical future states before executing them in the physical or operational environment.

## What is Planning?
Planning is the process of generating a causal sequence of actions from a given starting point to achieve a desired target state.

A standard planning problem requires four core components:
1. **Initial State**: The baseline state of the environment or agent before execution.
2. **Action Space**: A set of valid actions characterized by:
   * **Preconditions**: Logical constraints specifying when an action can be executed in a state.
   * **Effects**: Mutative rules defining how the action alters the current state.
3. **Goal State (Predicate)**: A target condition or predicate defining successful completion.
4. **Search Strategy**: A general-purpose search method (e.g., A{sup}`*`, BFS, DFS) used to explore the state-action graph.

### Planning vs. Decision Processes (KADP)
While closely related, Planning and Decision Processes operate at different stages of execution:
* **Planner**: Operates offline in a hypothetical state space. It searches for and outputs a static sequence of actions (a plan) without altering the live system.
* **Decision Process**: Operates online cycle-by-cycle. It executes real steps, handles dynamic environment state mutations, and drives real-world actuation.

## Scientific Foundations

Automated Planning and Scheduling is a foundational discipline of Symbolic Artificial Intelligence.

* **Complementing Generative AI:** Current research highlights that LLMs struggle with multi-step deterministic search, constraint adherence, and strict correctness guarantees (see [Subbarao Kambhampati on Planning & LLMs](https://thegradientpub.substack.com/p/subbarao-kambhampati-planning-reasoning-llms)). Formal planning tools bridge this gap by offering sound reasoning engines.
* **Mission-Critical Applications:** Classical planning engines drive real-world autonomous systems where failure is not an option, such as NASA JPL's Mars Rover activity scheduling ([Mars 2020 Scheduler](https://ai.jpl.nasa.gov/public/projects/m2020-scheduler/) and [NASA CP&S Workshop Overview](https://www-robotics.jpl.nasa.gov/media/documents/02_estlin_cp&s_nasapswkshop.pdf)).
* **Theoretical Foundation:** For a deep dive into formal search spaces and planning theory, refer to this [Automated Planning Overview Video](https://www.youtube.com/watch?v=epXjq1ekqao).


## Why Use Formal Planning?

* **Explainability:** Generates transparent action sequences where every step can be traced back to explicit state transitions and decision logic.
* **Causal Determinism:** Ensures that actions are only selected if their preconditions are strictly met, eliminating hallucinations or illegal state transitions.
* **Domain Expertise Integration:** Enables developers to encode domain rules and common-sense logic directly without training massive data models.
* **Guarantees & Trust:** Offers mathematical guarantees regarding completeness, correctness, and cost-optimality, which are required for high-stakes, safety-critical tasks.

## Implementation Details

The library provides a base implementation of graph search via the `SearchPlanner` class, which iteratively explores sequential action spaces until a goal is met.

### Core Architecture

To initialize and run a `SearchPlanner`, supply the following inputs:

| Input Parameter | Type | Description |
| :--- | :--- | :--- |
| **Initial State (`PS`)** | Hashable Object | Starting state of the planner. **Must be immutable and hashable.** |
| **Goal Predicate** | Callable | Function taking a `PS` and returning `True` when a goal state is satisfied. |
| **Succession Function** | Callable | Function producing available planner actions (`PA`), transition costs (lower is better), and resulting states (`PS`). |
| **Frontier Factory** | Object | Strategy determining state expansion order. |

> **Note on State Mutability:** The planner state (`PS`) is closely related to DP state, but **must be hashable (and thus immutable)** to enable efficient set-based duplicate detection in search frontiers.


### Frontier Strategies

The library ships with several standard frontier factories to control search behavior:

* **`Stack`:** Performs Depth-First Search (DFS). Useful in memory-constrained settings where deep solution paths exist.
* **`Queue`:** Performs Breadth-First Search (BFS). Guarantees finding the solution with the fewest number of actions.
* **`PriorityQueue`:** Performs Uniform-Cost Search (UCS) to find the absolute lowest-cost plan.
  * *Heuristic Support:* If supplied with an *admissible heuristic*, `PriorityQueue` executes A{sup}`*` search, delivering optimal cost with minimal state exploration.


### Action Abstractions & Succession Functions

To simplify building custom succession functions, the library provides built-in action pattern abstractions:

* **`SearchPlannerStaticOption`:** Represents a static planner action available across multiple planner states.
  * *Helper:* `static_opts_succession` constructs a full succession function from a set of static options.
* **`SearchPlannerDynamicOption`:** Represents pattern-based or dynamically generated actions dependent on current state features.
  * *Helper:* `dynamic_opts_succession` constructs a succession function from dynamic option generators.

> **Analogy:** `SearchPlannerStaticOption` maps to fixed operators, while `SearchPlannerDynamicOption` maps to operator generators within a Decision Process.
