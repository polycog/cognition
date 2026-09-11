# ``cognition`` Documentation

Welcome to `cognition` 🧠, an open-source Python framework developed by Polycog, Inc. designed to facilitate the creation of trustworthy cognitive agents via a modular API that handles complex decision-making, natural language processing, structural knowledge representation, and automated reasoning.

Key affordances:

* **Enforce** (hierarchical) agent orchestration via a knowledge-augmented ``DecisionProcess`` - a declarative, [state-driven execution machine that continually matches against policy directives](https://doi.org/10.1016/j.tics.2003.08.012).
* Declare [domain knowledge](https://doi.org/10.48550/arXiv.2506.18019) using **validated data models** (``Entity``, ``BinaryRelation``), related & queried within a dynamic ``WorldGraph``.
* Integrate the cognitive [agent loop](https://en.wikipedia.org/wiki/Intelligent_agent) with custom environmental sensors and/or actuators via a ``Cogent`` (similar to a **harness** in LLM-based systems).
* Use **your choice of language model(s)** for **classification** (e.g., intent recognition via ``EnumClassifier``), **description** (e.g., human-readable situational awareness via ``describe_facts``), and **population** (e.g., extract structured data via ``ModelPopulator``) tasks, where context is [automatically infused](https://doi.org/10.48550/arXiv.2501.10868) with **expert knowledge**.
* Integrate symbolic **reasoning** to efficiently & verifiably solve sub-problems, such as using a ``SearchPlanner`` to find an [optimal sequence of steps to achieve a goal](https://doi.org/10.1109/TSSC.1968.300136).

:::{note}
This project is under active development!
:::

```{toctree}
:hidden:
ideas/index
cook/index
:hidden:
```
