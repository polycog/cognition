<div align="center">

# Polycog cognition

[![Checks](https://github.com/polycog/cognition/actions/workflows/checks.yml/badge.svg)](https://github.com/polycog/cognition/actions/workflows/checks.yml)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue.svg)](https://fsl.software)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fpolycog%2Fcognition%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
[![Discord](https://img.shields.io/discord/1498434981788123206?color=7289da&logo=discord&logoColor=white)](https://discord.gg/Uqhjq9vBnV)

<p>
    <a href="https://polycog.ai" target="_blank">Website</a> &bull;
    <a href="https://github.com/polycog/tutorials" target="_blank">Tutorials</a> &bull;
    <a href="https://docs.polycog.ai" target="_blank">Docs</a>
</p>

</div>

<!-- start intro -->
Welcome to `cognition` 🧠 an open-source agent framework in Python developed by [Polycog, Inc.](https://polycog.ai). The framework implements a [neurosymbolic](https://en.wikipedia.org/wiki/Neuro-symbolic_AI) foundation for complex decision-making, natural language processing, structural knowledge representation, and logical & deterministic reasoning.
It enables developers to build trustworthy cognitive agents - agents that are reliable (repeatable, provably correct reasoning), steerable (programmatic enforcement of behavior directives), and explainable (causal provenance of all decisions).  

## 📖 Table of Contents
- [Core Concepts](#core-concepts)
- [Library Structure](#library-structure)
- [Getting Started](#getting-started)
- [Documentation & Resources](#documentation--resources)

## Core concepts
### 1. Knowledge-Augmented `DecisionProcess`
* **What it does:** Design agent behavior via a declarative, [state-driven execution machine](https://doi.org/10.1016/j.tics.2003.08.012) that matches the current environment state against explicit policy directives.
* **Agentic AI Equivalent:** Orchestrator
* **Why use it:** Replaces non-deterministic LLM loops and brittle if-else scripts with declarative state control — enforcing safety guardrails, business logic, and policies at every step. ![](https://img.shields.io/badge/-Compliance_without_Rigidity-E9D5FF?style=flat-square)

### 2. Structured Knowledge Representation with `WorldGraph`
* **What it does:** Declares [domain knowledge](https://doi.org/10.48550/arXiv.2506.18019) using strongly-typed, validated data models that can be inspected, queried, and mutated at runtime.
* **Agentic AI Equivalent:** engineered or raw prompt context
* **Why use it:** Gives agents a typed, queryable source of truth instead of relying on fragile context windows or unvalidated text blobs. ![](https://img.shields.io/badge/-Stable_%26_Grounded-E9D5FF?style=flat-square)

### 3. Agent Runtime Loop with `Cogent`
* **What it does:** Manages the [intelligent agent loop](https://en.wikipedia.org/wiki/Intelligent_agent), bridging internal cognitive processes with external environmental sensors and actuators.
* **Agentic AI Equivalent:** Harness
* **Why use it:** Separates core cognitive reasoning from raw API calls. This creates a clean boundary for safety checks, API mocking, and simulation testing. ![](https://img.shields.io/badge/-Decoupled_%26_Modular-E9D5FF?style=flat-square)

### 4. Language Processing with Data Models
* **What it does:** Uses LLMs for specific, constrained tasks—such as intent classification (`EnumClassifier`), generating natural language from facts (`describe_facts`), and extracting structured data (`ModelPopulator`) with [automated context engineering](https://doi.org/10.48550/arXiv.2501.10868).
* **Agentic AI Equivalent:** Structured Outputs
* **Why use it:** Restricts LLM operations to strict input/output contracts, keeping non-deterministic text generation out of core control flow. ![](https://img.shields.io/badge/-Structured_%26_Safe-E9D5FF?style=flat-square)

### 5. Verifiable Logical Reasoning with `SearchPlanner`
* **What it does:** Solves planning sub-problems algorithmically to find an [optimal sequence of actions](https://doi.org/10.1109/TSSC.1968.300136) to reach a specified target state.
* **Agentic AI Equivalent:** Chain-of-Thought
* **Why use it:** Guarantees causal validity, completeness, and efficiency for complex multi-step problems without relying on probabilistic LLM guessing. ![](https://img.shields.io/badge/-Provably_Correct_%26_Explainable-E9D5FF?style=flat-square)
<!-- end intro -->

> **Note:** This project is under active development. Expect regular updates and new features!



## 🏗️ Library Structure

The library is organized into specialized subpackages to handle distinct cognitive tasks:

### `cognition.cogent`
Core modeling for your (cog)nitive ag(ent) and its surroundings.
* **`cogent`**: Defines the fundamental agent loop and behaviors.
* **`env`**: Tools for creating and interacting with environmental sensors & actuators.

### `cognition.decision`
Frameworks for managing states and decision-making processes over time.
* **`chain`**: Mechanisms for linking sequences of decisions.
* **`core`**: Core functionality for decision-making.
* **`dp`**: Functionality for knowledge-augmented decision processes.
* **`stage`**: Mechanisms for decision processes based upon singular enumerated field.
* **`state`**: Re-usable state augmentations.

### `cognition.knowledge`
Handle structured data and complex ontologies.
* **`organization`**: Modules for structuring and linking concepts.
* **`representation`**: Primitives for representing facts, schemas, and semantic relationships.

### `cognition.language`
Tools for interpreting and generating natural language.
* **`classification`**: Text categorization and intent recognition.
* **`description`**: Capabilities for generating human-readable descriptions of states or actions.
* **`population`**: Tools for extracting data from text to populate knowledge representations.

### `cognition.reasoning`
Engines for logical deduction and automated planning.
* **`planning`**: Includes `SearchPlanner` and various state exploration strategies (DFS, BFS, UCS, A*) using classes like `FrontierManager`, `PriorityQueue`, and `SearchState`. Allows you to define `Static` and `Dynamic` transition options to navigate state spaces.

### `cognition.util`
Helpful utilities to streamline your code, including...
* **`enumeration`**: self-documenting and executing data.
* **`functypes`**: convenience function type descriptors.
* **`misc`**: utility code.

## 🚀 Getting Started

```bash
pip install polycog-cognition
```

Suggested exploration plan:

1. **[Tutorials](https://github.com/polycog/tutorials)**: thematic step-by-step guides, interactive Jupyter Notebooks, and complete Python reference implementations.
2. **[Examples](https://github.com/polycog/cognition/blob/main/examples/README.md)**: fully coded mini-applications.
3. **[Cookbook](https://docs.polycog.ai/cook)**: annotated recipes related to library features.

## 📚 Documentation & Resources

For detailed technical descriptions & deep dives into the design philosophy:

* **[Documentation Home](https://docs.polycog.ai)**
* **[Key API Ideas](https://docs.polycog.ai/ideas)**
* **[Comprehensive API Reference](https://docs.polycog.ai/autoapi)**


---

© 2026 - Polycog, Inc.
