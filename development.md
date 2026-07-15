# Polycog cognition

[![Checks](https://github.com/polycog/cognition/actions/workflows/checks.yml/badge.svg)](https://github.com/polycog/cognition/actions/workflows/checks.yml)

Run below (stopping on errors) via `source checks.sh` (given installs via `dev-requirements.txt`).

## Testing

1. `export PYTHONPATH="${PYTHONPATH}:src"`
2. `python -m unittest discover`

### Coverage

(After #1 above)

1. `coverage run --source=cognition -m unittest discover`
2. Options...
   * `coverage report -m`
   * `coverage html`

## Pre-Commit Checks

1. `mypy tests src`
2. `pylint tests src`
3. `ruff check tests src`
4. `black --check tests src`
5. `validate-pyproject pyproject.toml`
