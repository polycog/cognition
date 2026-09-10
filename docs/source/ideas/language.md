# Language

The library provides multiple utilities to integrate language processing & generation within cogent decision-making.
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
