"""
Planning code for WaterJug
"""

from __future__ import annotations

from typing import Optional

from collections.abc import Iterable, Sequence

from abc import abstractmethod, ABC

from dataclasses import dataclass

from enum import IntEnum

from math import gcd

import streamlit as st

from cognition import (
    Predicate,
    SearchState,
    Task,
    create_search_task,
    stringify,
)

##################################################

@dataclass(frozen=True)
class Jug:
    """
    A jug
    """

    volume: int
    contents: int

    def __str__(self) -> str:
        return f"{self.contents}/{self.volume}"

# A pair of jugs!!
type JugPair = tuple[Jug, Jug]

class WhichJug(IntEnum):
    """
    Convenience enumeration for
    indexing one of a pair
    """

    FIRST = 0
    SECOND = 1

    @property
    def other(self) -> WhichJug:
        """
        Flips from first->second or vice-versa
        """

        return WhichJug.FIRST if self == WhichJug.SECOND else WhichJug.SECOND


class JugPairAction(ABC):
    """
    An action on a pair of jugs
    """

    @abstractmethod
    def can_perform(self, jugs: JugPair) -> bool:
        """
        Indicates if the action can be
        performed given the state
        """

    @abstractmethod
    def perform(self, jugs: JugPair) -> JugPair:
        """
        Performs the action,
        producing the resulting state
        """


@dataclass(frozen=True)
class PourAction(JugPairAction):
    """
    Pouring water from one jug to another
    """

    pour_from: WhichJug

    def __str__(self) -> str:
        return f"Pour from {self.pour_from.name} to {self.pour_from.other.name}"

    def can_perform(self, jugs: JugPair) -> bool:
        j_from: Jug = jugs[self.pour_from.value]
        j_to: Jug = jugs[self.pour_from.other.value]

        return (j_from.contents > 0) and (j_to.contents < j_to.volume)

    def perform(self, jugs: JugPair) -> JugPair:
        j_from: Jug = jugs[self.pour_from.value]
        j_to: Jug = jugs[self.pour_from.other.value]

        pour_amt: int = min(j_from.contents, j_to.volume - j_to.contents)

        def by_jug(target: WhichJug) -> int:
            return (j_from.contents - pour_amt) \
                if (target == self.pour_from) \
                    else (j_to.contents + pour_amt)

        return (
            Jug(jugs[0].volume, by_jug(WhichJug.FIRST)),
            Jug(jugs[1].volume, by_jug(WhichJug.SECOND)),
        )


@dataclass(frozen=True)
class FillAction(JugPairAction):
    """
    Filling a jug
    """

    fill_to: WhichJug

    def __str__(self) -> str:
        return f"Fill {self.fill_to.name}"

    def can_perform(self, jugs: JugPair) -> bool:
        j: Jug = jugs[self.fill_to]

        return j.contents < j.volume

    def perform(self, jugs: JugPair) -> JugPair:
        new_jug: Jug = Jug(
            jugs[self.fill_to.value].volume,
            jugs[self.fill_to.value].volume
        )

        return (
            new_jug if self.fill_to == WhichJug.FIRST else jugs[0],
            new_jug if self.fill_to == WhichJug.SECOND else jugs[1],
        )


@dataclass(frozen=True)
class EmptyAction(JugPairAction):
    """
    Emptying a jug
    """

    empty_from: WhichJug

    def __str__(self) -> str:
        return f"Empty {self.empty_from.name}"

    def can_perform(self, jugs: JugPair) -> bool:
        return jugs[self.empty_from.value].contents > 0

    def perform(self, jugs: JugPair) -> JugPair:
        new_jug: Jug = Jug(
            jugs[self.empty_from.value].volume,
            0
        )

        return (
            new_jug if self.empty_from == WhichJug.FIRST else jugs[0],
            new_jug if self.empty_from == WhichJug.SECOND else jugs[1],
        )

###

def wj_successor(pair: JugPair) -> Iterable[tuple[JugPair, JugPairAction, int]]:
    """
    Produce all possible outcomes from
    a given waterjug state
    """

    for a in (
        EmptyAction(WhichJug.FIRST),
        EmptyAction(WhichJug.SECOND),

        FillAction(WhichJug.FIRST),
        FillAction(WhichJug.SECOND),

        PourAction(WhichJug.FIRST),
        PourAction(WhichJug.SECOND),
    ):
        if a.can_perform(pair):
            yield (a.perform(pair), a, 1)


def create_wj_goal(target: int) -> Predicate[JugPair]:
    """
    Produces a Waterjug goal check
    based on the supplied volume target
    """

    @stringify(f"volume={target}")
    def goal_test(pair: JugPair) -> bool:
        return target in (j.contents for j in pair)

    return goal_test

##################################################

@dataclass(frozen=True)
class InvalidConfiguration:
    """
    Result of an invalid problem configuration
    """

    msg: str

@dataclass(frozen=True)
class TooLong:
    """
    Result of a valid problem configuration
    requiring too many steps of inference
    """

    cycles: int

@dataclass(frozen=True)
class Success:
    """
    Result of a valid problem configuration
    producing a plan
    """

    cycles: int
    plan: Sequence[tuple[str, int, int]]

type WJResult = InvalidConfiguration | TooLong | Success

#

def validate_inputs(
    vol1: int,
    vol2: int,
    desired: int,
    max_steps: int
) -> Optional[str]:
    """
    Produces an error message if the
    supplied solver inputs are invalid;
    otherwise returns nothing
    """

    if (vol1 < 1) or (vol2 < 1):
        return "Jugs must both have positive capacity."

    if desired < 0:
        return "Goal volume must be non-negative."

    if (desired > vol1) and (desired > vol2):
        return "At least one jug must have the target capacity."

    if max_steps < 1:
        return "Max steps must be positive."

    v_gcd = gcd(vol1, vol2)
    if desired % v_gcd != 0:
        return (
            "Actually impossible!! "
            f"{desired} cannot be produced from jugs of {vol1} and {vol2}. "
            f"This is because the greatest common divisor of the jugs is {v_gcd}, "
            "which does not cleanly divide the target."
        )

    return None

@st.cache_data
def run_waterjug(
    vol1: int,
    vol2: int,
    desired: int,
    max_steps: int
) -> WJResult:
    """
    Solves the supplied waterjug instance,
    validing the inputs first
    """

    bad_input_msg: Optional[str] = validate_inputs(vol1, vol2, desired, max_steps)
    if isinstance(bad_input_msg, str):
        return InvalidConfiguration(bad_input_msg)

    #

    init_jugs: JugPair = (
        Jug(vol1, 0),
        Jug(vol2, 0)
    )

    wj: Task[SearchState[JugPair, JugPairAction]] = create_search_task(
        init_jugs,
        create_wj_goal(desired),
        wj_successor
    )

    wj.run_cycles(max_steps)

    #

    if not wj.done:
        return TooLong(wj.num_cycles)

    if not wj.state.action_path:
        return InvalidConfiguration("There is no possible solution :'(")

    sim_state: JugPair = init_jugs

    plan = [
        ("Initial State", sim_state[0].contents, sim_state[1].contents)
    ]

    for a in wj.state.action_path:
        sim_state = a.perform(sim_state)
        plan.append((
            str(a),
            sim_state[0].contents,
            sim_state[1].contents
        ))

    return Success(
        wj.num_cycles,
        plan
    )
