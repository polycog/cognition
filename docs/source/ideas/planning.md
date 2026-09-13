# Planning
> **Agentic AI Equivalent**.
> In agentic AI, Chain of Thought (CoT), prompting a model to think step-by-step to generate longer intermediate reasoning traces, serves as the primary, language-based mechanims for reasoning.

## What is Planning?
While Large Language Models (LLMs) execute Chain of Thought (CoT) through probabilistic next-token prediction, formal planning in `cognition` implements explicit, algorithmic step-by-step reasoning. Instead of relying on statistical completion, the planning engine systematically decomposes high-level goals into valid action chains by evaluating hypothetical future states before any action is executed in the physical or operational environment.

At its core, planning is the process of generating a causal sequence of actions from a given starting point to achieve a desired target state. Every formal planning problem within **cognition** is constructed using four fundamental components.

1. **Initial State**
   The baseline state snapshot of the environment and agent context prior to plan execution. This is typically described using a `WorldGraph`

2. **Action Space**
   The set of all permissible operational actions available to the agent. Each action (a `SearchPlanOption`) is explicitly parameterized by:
   * **Preconditions** implemented as Python factories: Logical constraints specifying the exact state criteria required before an action can be executed.
   * **Effects** implemented as Python methods: Mutative state-transition rules that define how executing the action alters the current state.

3. **Goal State**
   A target logical condition that explicitly defines the criteria for successful task completion.

4. **Search Strategy**
   General-purpose graph traversal and optimization algorithms (e.g., $A^*$, Breadth-First Search, Depth-First Search) used to systematically explore the state-action graph and discover an optimal path from the initial state to the goal state.

### Planning vs. Decision Processes (KADP)
While closely related, Planning and Decision Processes operate at different stages of execution:
* **Planner**: Operates offline in a hypothetical state space. It searches for and outputs a static sequence of actions (a plan) without altering the live system.
* **Decision Process**: Operates online cycle-by-cycle. It executes real steps, handles dynamic environment state mutations, and drives real-world actuation.

## What are the scientific principles?

[Automated Planning and Scheduling](https://www.icaps-conference.org/) an Artificial Intelligence discipline that provides a mathematically rigorous framework for autonomous decision-making through deterministic state-space search. While modern Large Language Models (LLMs) excel at natural language parsing and intuition, they inherently struggle with multi-step search, strict constraint adherence, and provable correctness guarantees. Formal planning engines bridge this gap by serving as sound reasoning systems that guarantee valid, executable plan generation—making them essential for mission-critical, high-stakes autonomous systems like NASA JPL's Mars Rover activity scheduling, where operational failure is unacceptable.

```{seealso} Further Reading & References
- **The Gradient:** [On the Role of LLMs in Planning & Reasoning](https://thegradientpub.substack.com/p/subbarao-kambhampati-planning-reasoning-llms) — Prof. Subbarao Kambhampati analyzes why LLMs struggle with multi-step deterministic search and the need for symbolic planners.
- **NASA JPL AI Group:** [Mars 2020 Onboard Activity Scheduler](https://ai.jpl.nasa.gov/public/projects/m2020-scheduler/) — Technical overview of mission-critical, constraint-based automated planning on the Perseverance rover.
- **NASA Robotics:** [Constraint-Based Planning & Scheduling for Spacecraft Autonomy](https://www-robotics.jpl.nasa.gov/media/documents/02_estlin_cp&s_nasapswkshop.pdf) — Workshop PDF detailing state-space constraints and autonomous scheduling architectures for space systems.
- **Automated Planning Lecture:** [State-Space Search & Planning Foundations](https://www.youtube.com/watch?v=epXjq1ekqao) — Comprehensive video breakdown of formal state-action representations and graph search algorithms.
```


## Why Use Planning?
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
