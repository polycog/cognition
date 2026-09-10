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

Welcome to **Cognition**! 🧠

Cognition is an active, open-source Python framework developed by Polycog, Inc. designed to facilitate the creation of intelligent cognitive agents. It provides a robust, modular API that handles complex decision-making, natural language processing, structural knowledge representation, and automated reasoning.

> **Note:** This project is under active development. Expect regular updates and new features!

## 📖 Table of Contents
- [Overview](#overview)
- [Library Structure](#library-structure)
- [Getting Started](#getting-started)
- [Documentation & Resources](#documentation--resources)

## 🔬 Overview

Cognition is built on the idea of separating different cognitive and operational workflows into highly focused, intuitive submodules. Whether you're building an agent to navigate dynamic environments, parse semi-structured information, or deduce optimal action plans, Cognition provides the fundamental building blocks.

## 🏗️ Library Structure

The library is organized into specialized subpackages to handle distinct cognitive tasks:

### `cognition.cogent`
Core modeling for your agent and its surroundings.
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
