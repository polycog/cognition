"""
Illustrates a simple hierarchical
decomposition of decision processes
in a Bingo caller assistant.

Sub-problem of getting valid input
takes care of both letters and numbers,
while the play process handles de-
duplication and interactive game state.

Integrated is a simple example of testing
the input sub-process in isolation.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import StringIO
from random import shuffle
from string import ascii_uppercase
from typing import ClassVar, cast, override

from cognition import Cogent, DecisionProcess, IOContainer, Operator

# ===


@dataclass
class InputState:
    """
    Sub-problem of getting a valid value
    """

    utterance: str | None = None
    """supplied input; None for nothing yet"""

    validated: bool = False
    """has the utterance been checked yet"""

    @staticmethod
    def done(state: InputState, _io: IOContainer) -> bool:
        """is the input problem complete?"""

        return (state.utterance is not None) and state.validated


# ===

dp_input = DecisionProcess(InputState).add_termination_check(InputState.done)


# START encapsulate
ARG_LETTER: str = "letter"
"""name of the argument to supply to the sub-problem"""


def get_valid_input(letter: str | None) -> str:
    """
    convenience method to provide the
    letter as the appropriate argument
    to the sub-dp and extract the result
    """

    dp_input.reinit()
    result = dp_input(max_cycles=None, suppress_errors=True, **{ARG_LETTER: letter})

    assert result is not None

    return cast(str, result.utterance)


# END encapsulate

# ====


def _get_letter(io: IOContainer) -> str | None:
    """arg getter"""

    return cast(str | None, io.args[ARG_LETTER])


@dp_input.operator("get")
class GetInput(Operator[InputState]):
    """gets the utterance"""

    @override
    def can_perform(self, state: InputState, _io: IOContainer) -> bool:
        return state.utterance is None

    @override
    def perform(self, state: InputState, io: IOContainer) -> None:
        prompt = f"Please provide the { "letter" if _get_letter(io) is None else "number" }: "
        state.utterance = input(prompt)


@dp_input.operator("val_letter")
class ValidateInputLetter(Operator[InputState]):
    """validates the utterance as a bingo letter"""

    @override
    def can_perform(self, state: InputState, io: IOContainer) -> bool:
        return (state.utterance is not None) and (_get_letter(io) is None)

    @override
    def perform(self, state: InputState, io: IOContainer) -> None:
        if state.utterance in ("B", "I", "N", "G", "O"):
            state.validated = True
        else:
            state.utterance = None


@dp_input.operator("val_num")
class ValidateInputNumber(Operator[InputState]):
    """validates the utterance as a bingo number"""

    # START valid_bounds
    BOUNDS: ClassVar[dict[str, tuple[int, int]]] = {
        "B": (1, 15),
        "I": (16, 30),
        "N": (31, 45),
        "G": (46, 60),
        "O": (61, 75),
    }
    # END valid_bounds

    @override
    def can_perform(self, state: InputState, io: IOContainer) -> bool:
        return (state.utterance is not None) and (_get_letter(io) is not None)

    @override
    def perform(self, state: InputState, io: IOContainer) -> None:
        letter = cast(str, _get_letter(io))

        try:
            number = int(cast(str, state.utterance))

            lower, upper = self.BOUNDS[letter]
            if lower <= number <= upper:
                state.validated = True
            else:
                state.utterance = None

        except ValueError:
            state.utterance = None


# ===

# pylint: disable=invalid-name
# START sub_problem_testing
tests_passed: int = 0


@contextmanager
def _simulate_stdin(inputs: Sequence[str]):
    """Context manager to mock sys.stdin with a sequence of strings."""

    # Combine inputs with newlines to simulate pressing 'Enter'
    mock_input = "\n".join(inputs) + "\n"

    # Save the original stdin so we can restore it later
    original_stdin = sys.stdin
    try:
        sys.stdin = StringIO(mock_input)
        yield
    finally:
        sys.stdin = original_stdin


def _test_input_dp(letter: str | None, expected: str, *inputs: str) -> None:
    """
    wrapper around assert to mock stdin/out,
    then call get_valid_input with supplied args
    """

    with _simulate_stdin(inputs), contextlib.redirect_stdout(StringIO()):
        actual = get_valid_input(letter)

    assert (
        actual == expected
    ), f"letter={letter}, inputs={inputs}; actual ({actual}) != expected ({expected})"

    global tests_passed  # pylint: disable=global-statement
    tests_passed += 1


def _input_dp_tests() -> None:
    """
    tests...
    * bad letters
    * good letters
    * good + bad letter/number combos
      (with significant input mistakes)
    """

    bad_letters = [l for l in ascii_uppercase if l not in ValidateInputNumber.BOUNDS]

    for l, (low, high) in ValidateInputNumber.BOUNDS.items():
        # easy good letter
        _test_input_dp(None, l, l)

        # variable known bad letters
        shuffle(bad_letters)
        _test_input_dp(None, l, *(bad_letters + [l]))
        bad_letters.pop()

        bad = [str(b) for b in range(101) if not low <= b <= high]

        for n in range(low, high + 1):
            # easy good letter + number
            _test_input_dp(l, str(n), str(n))

            # given letter; variable known bad numbers
            shuffle(bad)
            _test_input_dp(l, str(n), *(bad + [str(n)]))
            bad.pop()


_input_dp_tests()
# END sub_problem_testing

# ===


@dataclass
class PlayState:
    """
    Game of Bingo
    """

    called: set[str] = field(default_factory=set)
    """prior spots called"""

    next_call: str | None = None
    """next spot; or None for pending"""

    done: bool = False
    """has someone won?"""

    @staticmethod
    def game_over(state: PlayState, _io: IOContainer) -> bool:
        """func for detecting end of game play"""

        return state.done


# ===

dp_play = DecisionProcess(PlayState).add_termination_check(PlayState.game_over)


@dp_play.operator("draw")
class PlayDraw(Operator[PlayState]):
    """draw the next spot"""

    @override
    def can_perform(self, state: PlayState, _io: IOContainer) -> bool:
        return state.next_call is None

    @override
    def perform(self, state: PlayState, _io: IOContainer) -> None:
        while True:
            letter = get_valid_input(None)
            number = get_valid_input(letter)

            candidate = f"{letter}{number}"
            if candidate not in state.called:
                break

            print(f"Already called: {candidate}")

        state.next_call = candidate


@dp_play.operator("announce")
class PlayAnnounce(Operator[PlayState]):
    """announce the draw"""

    @override
    def can_perform(self, state: PlayState, _io: IOContainer) -> bool:
        return state.next_call is not None

    @override
    def perform(self, state: PlayState, _io: IOContainer) -> None:

        # excuse the nested operator logic
        # for a shorter example
        result = input(f"Draw {state.next_call} (bingo?): ")
        if result.strip().lower() == "bingo":
            print(f"Prior: {state.called}")

            confirm = input("Confirmed (y/n)? ")
            if confirm.strip().lower() == "y":
                state.done = True

        state.called.add(cast(str, state.next_call))
        state.next_call = None


# ===

if __name__ == "__main__":
    print(f"Tests passed: {tests_passed}")
    print()

    Cogent(dp_play, name="bingo")()  # let's play!
