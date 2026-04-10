intro () {
    echo "===================="
    echo ""
    echo ">> $@"
    echo ""
    "$@"
}

afterword() {
    echo ""
    echo "===================="
    echo ""
    echo ""
}

success_or_die () {
    intro $@

    if [ $? -ne 0 ]; then
        afterword
        exit 1
    fi

    afterword
}

if [ -z "$POLYCOG_COGNITION_DEV" ]; then
    export PYTHONPATH="${PYTHONPATH}:src"
    export POLYCOG_COGNITION_DEV="t"
fi

#####

success_or_die mypy tests src
success_or_die pylint tests src
success_or_die ruff check tests src

success_or_die coverage run --source=cognition -m unittest discover

intro coverage report -m
afterword
