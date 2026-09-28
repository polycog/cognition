"""
Evaluating choices
"""

from typing import Any, cast

from cognition import (
    Action,
    Cogent,
    DecisionProcess,
    IOContainer,
    NamedObject,
    Operator,
    Rank,
    operator_sorting_key,
    sorting_evaluator,
    uniform_evaluator,
)

# ===

PARAM_CHOICE = "result"


class Choice(Operator[str]):
    """one-step decision"""

    def __init__(self, result: str) -> None:
        super().__init__(
            type(self).__name__, **{PARAM_CHOICE: result, "terminal": True}
        )

    def can_perform(self, _state: str, _io: IOContainer) -> bool:
        return True

    def perform(self, _state: str, _io: IOContainer) -> str:
        return self.params[PARAM_CHOICE]

    # START op_sorting_defn
    def __eq__(self, other) -> bool:
        if not isinstance(other, Choice):
            return NotImplemented

        return self.params[PARAM_CHOICE] == other.params[PARAM_CHOICE]

    def __lt__(self, other) -> bool:
        if not isinstance(other, Choice):
            return NotImplemented

        return self.params[PARAM_CHOICE] < other.params[PARAM_CHOICE]

    # END op_sorting_defn


# ===


def all_same(dp: DecisionProcess) -> None:
    """all operators get `MEDIUM` ranking"""

    # START all_same
    dp.add_action_evaluator(uniform_evaluator(Rank.MEDIUM))
    # END all_same


def op_classes(dp: DecisionProcess) -> None:
    """mix uniform via predicate: a=LOW, other=HIGH"""

    # START op_classes
    def is_a(a: Any) -> bool:
        return cast(NamedObject, a).params[PARAM_CHOICE] == "a"

    def not_a(a: Any) -> bool:
        return not is_a(a)

    dp.add_action_evaluator(uniform_evaluator(Rank.LOW, p=is_a))
    dp.add_action_evaluator(uniform_evaluator(Rank.HIGH, p=not_a))
    # END op_classes


def op_sorting_abs(dp: DecisionProcess) -> None:
    """explicit association of rank to values"""

    # START op_sorting_abs
    def _key(a: Action[str], _state: str, _io: IOContainer) -> int:
        return {
            "a": 100,
            "b": 50,
            "c": 1,
            "d": 0,  # ok that it doesn't exist
        }[cast(NamedObject, a).params[PARAM_CHOICE]]

    dp.add_action_evaluator(sorting_evaluator(_key))
    # END op_sorting_abs


def op_sorting_rel(dp: DecisionProcess) -> None:
    """rank via relative object-based comparison"""

    # START op_sorting_rel
    dp.add_action_evaluator(sorting_evaluator(operator_sorting_key()))
    # END op_sorting_rel


# ===

cogent = Cogent(DecisionProcess(lambda: "_start_"))

cogent.dp.add_operator(Choice("a"))
cogent.dp.add_operator(Choice("b"))
cogent.dp.add_operator(Choice("c"))

# TODO: choose an evaluation function above!
# (None = CRASH due multiple options, lack of ranking)
# all_same(cogent.dp)  # all same rank (so random)
# op_classes(cogent.dp)  # categories of rank
# op_sorting_abs(cogent.dp)  # absolute
op_sorting_rel(cogent.dp)  # relative

# ===

print(f"{cogent.dp.state} -> ")
for i in range(5):
    cogent()
    print(f"{i+1}) {cogent.dp.state=}")
