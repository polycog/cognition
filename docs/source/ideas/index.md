# Key API Ideas

<!-- https://myst-parser.readthedocs.io/en/latest/syntax/typography.html -->

This section highlights some of the key technical aspects of the library.

:::{tip}
The tutorials provide an annotated step-by-step guide with a domain.
:::

```{toctree}
:hidden:
kadp.md
cogent.md
knowledge.md
planning.md
language.md
```

## Overview

* [](./kadp.md): (hierarchical) agent orchestration using a declarative, state-driven execution machine that continually matches against policy directives.
* [](./cogent.md): integrating the cognitive agent loop with custom environmental sensors and/or actuators (similar to a harness in LLM-based systems).
* [](./knowledge.md): declaring, relating, and querying dynamic domain knowledge.
* [](./planning.md): integrating symbolic reasoning to efficiently & verifiably solve sub-problems.
* [](./language.md): model-agnostic language tasks that are automatically infused with domain knowledge.


## Guiding Principles

Flexible
: The library gives you wings to build impactful agents your way, for your problems, with your tools.

Opinionated
: Through layered modules, the API guides you towards our view of strong agent design.

Collaborative
: The library, in coordination with amazing imports, tries to play nice with Python tooling (e.g., IDE, type checking).

Declarative('ish)
: Where reasonable, the library makes encourages you to describe *what* (vs *how*).

Clean/Fun
: Where possible, abstract away boilerplate.
