# cognition

## Testing

1. `export PYTHONPATH="${PYTHONPATH}:src"`
2. `python -m unittest discover`

## Pre-Commit Checks

1. `mypy tests src`
2. `pylint tests src`
3. `ruff check tests src`
