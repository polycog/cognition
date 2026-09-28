"""
Planning coins with static options
"""

from collections import Counter
from enum import IntEnum

from cognition import (
    Queue,
    SearchPlanner,
    SearchPlannerStaticOption,
    static_opts_succession,
)

# ===


class USCoin(IntEnum):
    """US coin name/value"""

    QUARTER = 25
    DIME = 10
    NICKLE = 5
    PENNY = 1


class AddCoin(SearchPlannerStaticOption[int, USCoin]):
    """
    Option to add a particular coin at any time

    State type: int (total cents)
    Action type: USCoin (above)
    """

    def __init__(self, coin: USCoin):
        super().__init__(coin)

    def is_available(self, _: int) -> bool:
        # can always add a coin (assume endless supply)
        return True

    def then(self, state: int) -> tuple[int, int]:
        # (result = old state + coin value, cost = 1 coin)
        return (state + self.action.value, 1)


# ===

TARGET_CENTS: int = 119

planner = SearchPlanner(
    # start with no money
    0,
    # goal is for total cents = target
    lambda s: s == TARGET_CENTS,
    # one static option per available coin
    static_opts_succession(*(AddCoin(c) for c in USCoin)),
    # BFS
    Queue,
)

# attempts to build a plan
planner.run()

# run can optionally take maximum steps,
# to maintain reactivity via iterative
# execution; in that context, it would
# still be searching if it hadn't found
# a plan but still had options to explore
assert not planner.still_searching

# False if the planner hasn't produced
# a plan that achieves the goal
assert planner.plan_found

cents = sum(c.value for c in planner.plan)
assert cents == TARGET_CENTS

# Plan (119¢): {<USCoin.QUARTER: 25>: 4, <USCoin.DIME: 10>: 1,
#               <USCoin.NICKLE: 5>: 1, <USCoin.PENNY: 1>: 4}
print(f"Plan ({TARGET_CENTS}¢): {dict(Counter(planner.plan))}")
