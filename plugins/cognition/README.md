# cognition plugin

Skills that help coding agents build with [`cognition`](https://github.com/polycog/cognition)
(PyPI: `polycog-cognition`), Polycog's framework for neurosymbolic agents.

| Skill | Use it to |
|---|---|
| `/cognition:build` | Write or change code that uses the library, reading the right sections of its agent guide first |
| `/cognition:review` | Review cognition code against the guide's idioms, anti-patterns and gotchas |
| `/cognition:debug` | Diagnose a decision process or cogent that returns `None`, hangs, or raises `NO_PROPOSAL` / `NO_RANK` |

The coding agent picks these up automatically when relevant; you can also invoke them by name.

## Install

```text
/plugin install cognition --marketplace polycog/cognition
```

Or in two steps: `/plugin marketplace add polycog/cognition`, then `/plugin install cognition@polycog`.

### For a team project

To offer the plugin to everyone working in a project, add this to the project's
`.claude/settings.json`. Each person is prompted once they trust the project folder.

```json
{
  "extraKnownMarketplaces": {
    "polycog": { "source": { "source": "github", "repo": "polycog/cognition" } }
  },
  "enabledPlugins": { "cognition@polycog": true }
}
```

### Other agent tools

The skills are plain `SKILL.md` folders, so tools that read skills from a directory can use them
too: copy the folders in `skills/` into that tool's skills directory. Without this plugin's
`cognition:` namespace, rename each folder and its `name:` field (e.g., `cognition-build`,
`cognition-review`, `cognition-debug`) to avoid clashing with other skills.

## Setup

The skills read the agent guide that ships inside the installed library
(`python -m cognition.guide "<heading>"`), so their guidance always matches the version your project
uses. Install `polycog-cognition` in the project's Python environment; without it, the skills fall
back to <https://docs.polycog.ai/AGENTS.md>, which matches the latest release.

The plugin's version matches the library release it was written for.
