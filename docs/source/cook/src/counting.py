"""
Illustrates a simple counting agent that
uses a termination check based upon the
result of an elaborator
"""

import logging
from dataclasses import dataclass
from math import sqrt
from typing import cast

from cognition import (
    Cogent,
    DecisionProcess,
    IOContainer,
    Operator,
    create_elaborator,
    stringify,
)

# ===

# Example of enabling logging to the console (stdout),
# capturing only those entries that rise to
# the level of a warning (rare)

handler = logging.StreamHandler()  # options exist for files, http, etc.
handler.setFormatter(
    logging.Formatter(
        "%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s"
    )  # more fields exist
)

logger = logging.getLogger("cognition")  # can be set to a sub-package for focus
logger.setLevel(logging.WARNING)  # set to DEBUG for details
logger.addHandler(handler)

# ===


@dataclass
class CountingState:
    """
    keeps track of where we are in the
    counting process (init, or current value)
    """

    counter: int | None = None
    """
    current value: None signals to init,
    otherwise current count
    """


def _is_perfect_square(num: int) -> bool:
    return sqrt(num) % 1 == 0


assert not _is_perfect_square(8)
assert _is_perfect_square(9)
assert not _is_perfect_square(10)


@stringify("is_perfect")  # easier-to-read in logs/debug output
def is_perfect_square(cs: CountingState, _io: IOContainer) -> bool:
    """
    example elaboration:
    examine raw counter state to determine if the value is a perfect square?
    """

    return (cs.counter is not None) and _is_perfect_square(cs.counter)


# ===

# note that the dp state "initializer" in this
# case is just the class constructor
counting_cogent = Cogent(DecisionProcess(CountingState))

# these could very well be methods of the state class,
# but for illustration, this will make available three
# keys on io.e.kwarg that automatically update each cycle
# during the elaboration phase
counting_cogent.dp.add_elaborator(
    create_elaborator(
        "examples",  # only visible in logs/debug output
        is_initialized=lambda cs, _: cs.counter is not None,
        is_perfect=is_perfect_square,
        as_str=lambda cs, _: str(cs.counter),
    )
)


@counting_cogent.dp.termination_check
@stringify("found_perfect")
def found_perfect(_cs: CountingState, io: IOContainer) -> bool:
    """
    utilizes elaboration to detect custom termination logic:
    in this case that a perfect square has been achieved
    """

    print(f"Terminate?: {io.e.as_str=} ({io.e.is_perfect=})")

    return cast(bool, io.e.is_perfect)


# ===


@counting_cogent.dp.operator("init")
class InitOperator(Operator[CountingState]):
    """
    sets the initial counter value
    based upon a supplied argument
    """

    def can_perform(self, _state: CountingState, io: IOContainer) -> bool:
        return not cast(bool, io.e.is_initialized)

    def perform(self, state: CountingState, io: IOContainer) -> None:
        start_val = cast(int, io.a.counter_start)

        print(f"Initialize: {start_val}")

        state.counter = start_val


@counting_cogent.dp.operator("increment")
class IncrementOperator(Operator[CountingState]):
    """
    Increments the counter
    """

    def can_perform(self, _state: CountingState, io: IOContainer) -> bool:
        return cast(bool, io.e.is_initialized)

    def perform(self, state: CountingState, _io: IOContainer) -> None:
        assert state.counter is not None  # for type checking

        new_val = state.counter + 1
        print(f"Increment: {state.counter} -> {new_val}")
        state.counter = new_val


# ===

examples = [1, 2, 5, 11, 101]

for starting_val in examples:
    print(f"== {starting_val=} ==")

    # when running the agent, kwarg passed to the
    # agent appear as io.a.kwarg
    output = cast(int, counting_cogent(counter_start=starting_val).dp.state.counter)

    # print(counting_cogent.dp) # uncomment to see lots of debug details about the DP

    print()
    print(f"The first perfect square ≥ {starting_val} is {output} ({sqrt(output)=}).")
    print()
