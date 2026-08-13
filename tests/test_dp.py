"""
Tests for dp code
"""

from __future__ import annotations

import unittest
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import (
    Any,
    Self,
    cast,
)

from cognition import (
    Action,
    ActionEvaluator,
    ActionFactory,
    ActionRank,
    AttrReferral,
    BaseDecisionProcess,
    BiFunction,
    DecisionProcess,
    Elaborator,
    IOContainer,
    NamedObject,
    Operator,
    OperatorGenerator,
    Phase,
    Rank,
    args_added,
    create_elaborator,
    create_named_action,
    format_name_params,
    operator_sorting_key,
    sorting_evaluator,
    stringify,
    uniform_evaluator,
)

from . import _test_pickle

# ===

# pylint: disable=too-many-lines


class OpStage(StrEnum):
    """Stage of op test"""

    SAY_HI = auto()
    SAY_BYE = auto()
    DONE = auto()


class HiOp(Operator[OpStage]):
    """Says hi"""

    def can_perform(self, state: OpStage, _io: IOContainer) -> bool:
        return state == OpStage.SAY_HI

    def perform(self, _state: OpStage, io: IOContainer) -> OpStage:
        print("hi", file=io.o.log)
        return OpStage.SAY_BYE


class ByeOp(Operator[OpStage]):
    """Says bye"""

    def can_perform(self, state: OpStage, _io: IOContainer) -> bool:
        return state == OpStage.SAY_BYE

    def perform(self, _state: OpStage, io: IOContainer) -> OpStage:
        print("bye", file=io.o.log)
        return OpStage.DONE


# ===


class PrioritizedMathOperation(Enum):
    """Prioritized options"""

    ADD = (1, lambda a, b: a + b)
    SUB = (2, lambda a, b: a - b)
    MULT = (3, lambda a, b: a * b)

    def __init__(self, priority: int, f: BiFunction[int, int, int]):
        self.priority = priority
        self.f = f

    def __call__(self, a: int, b: int) -> int:
        return self.f(a, b)


class ChangeOp(Operator[int]):
    """Modify state via a simple math operation"""

    def __init__(self, op: PrioritizedMathOperation, amt: int) -> None:
        super().__init__(op.name, amt=amt)

        self._op = op
        self._amt = amt
        self._enabled: bool = True

    def can_perform(self, state: int, _io: IOContainer) -> bool:
        return self._enabled

    def perform(self, state: int, _io: IOContainer) -> int:
        return self._op(state, self._amt)

    def flip(self) -> None:
        """flips enabled status"""

        self._enabled = not self._enabled

    @property
    def enabled(self) -> bool:
        """enabled status"""

        return self._enabled

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChangeOp):
            return NotImplemented

        return (self._op, self._amt, self._enabled) == (
            other._op,
            other._amt,
            other._enabled,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ChangeOp):
            return NotImplemented

        if (self._op, self._amt) == (other._op, other._amt):
            return self._enabled < other._enabled

        if self._op == other._op:
            return self._amt < other._amt

        return self._op.priority < other._op.priority

    def __hash__(self) -> int:
        return hash((self._op, self._amt))


# ===


def _zilch() -> int:
    return 0


class TestDP(unittest.TestCase):
    """Tests for dp code"""

    def setUp(self) -> None:
        self.vote_yay = create_named_action(
            "vote", lambda _s, _io: 1, value="yay", volume=12
        )

        self.vote_nay = create_named_action(
            "vote",
            lambda _s, _io: 0,
            value="nay",
        )

        self.abstain = create_named_action(
            "abstain",
            lambda _s, _io: -1,
        )

        self.io_source: Mapping[str, Any] = {}
        self.mock_io = IOContainer(
            AttrReferral(self.io_source),
            AttrReferral(self.io_source),
            AttrReferral(self.io_source),
            AttrReferral(self.io_source),
        )

    def test_pickle(self) -> None:
        """Confirms pickle/depickle"""

        _test_pickle(DecisionProcess(_zilch))

    def test_elaborable(self) -> None:
        """Confirming elaboration is added upon dp init"""

        s_name = "boring_name"
        e_name = "crafty_name"
        t_name = "tautology"

        v_name = "value"

        class MyState:
            """Example state"""

            def __init__(self) -> None:
                self._num = 42

            @staticmethod
            def func(s: MyState, io: IOContainer) -> int:
                """custom logic"""

                return s._num + (  # pylint: disable=protected-access
                    1 if io.i.clock.cycles >= 0 else 0
                )

            @property
            def elaborator(self) -> Elaborator[MyState]:
                """example to combine state + io"""

                @stringify(e_name)
                def _elab(state: MyState, io: IOContainer) -> dict[str, Any]:
                    return {v_name: self.func(state, io)}

                return _elab

            def __str__(self) -> str:
                return s_name

        s = MyState()
        dp = DecisionProcess(stringify("just_s")(lambda: s))

        @dp.termination_check
        @stringify(t_name)
        def _t_check(_state: MyState, _io: IOContainer) -> bool:
            return True

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={s_name}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={t_name}",
                    f"Elaborators={e_name}",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        dp.run_cycles(10)

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={s_name}",
                    f"Done?={True}",
                    f"Chosen={None}",
                    "Action Factories=",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={t_name}",
                    f"Elaborators={e_name}",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    f"Elaborated Data={v_name}:{MyState.func(dp.state, dp.io)}",
                    "Argument Values=",
                )
            ),
        )

    def test_args_call(self) -> None:
        """Confirming arguments context manager with __call__"""

        state_start = 0

        dp = DecisionProcess(stringify("const_start")(lambda: state_start))

        self.assertEqual(dp.state, state_start)

        # ===

        arg_name = "bar"
        arg_val = 42

        # pylint: disable=unused-variable
        @dp.operator("copy", terminal=True, arg_name=arg_name)
        class ArgCopy(Operator[int]):
            """Copies the arg"""

            def __init__(self, name: str, arg_name: str, **kwargs: Any) -> None:
                super().__init__(name, **kwargs)
                self._arg = arg_name

            def can_perform(self, _state: int, _io: IOContainer) -> bool:
                return True

            def perform(self, _state: int, io: IOContainer) -> int:
                return cast(int, getattr(io.a, self._arg))

        with args_added(dp, **{arg_name: arg_val}):
            dp.run_until_done()

        self.assertTrue(dp.done)
        self.assertEqual(dp.state, arg_val)

        # ===

        dp.reinit()

        self.assertEqual(dp.state, state_start)
        self.assertEqual(
            dp(
                max_cycles=2,
                suppress_errors=True,
                **{arg_name: arg_val},
            ),
            arg_val,
        )

        dp.reinit()

        self.assertEqual(dp.state, state_start)
        self.assertIsNone(
            dp(
                max_cycles=0,
                suppress_errors=True,
                **{arg_name: arg_val},
            ),
            arg_val,
        )
        self.assertFalse(dp.done)

        dp.reinit()
        self.assertEqual(dp.state, state_start)
        self.assertIsNone(dp())
        self.assertFalse(dp.done)

        dp.reinit()
        self.assertEqual(dp.state, state_start)
        with self.assertRaises(RuntimeError):
            self.assertIsNone(dp(suppress_errors=False))

    def test_named_op_decorator(self) -> None:
        """Confirming named operator decorator"""

        dp: DecisionProcess[bool] = DecisionProcess(
            stringify("start_false")(lambda: False)
        )

        op_name = "done"
        act_name = format_name_params(op_name, terminal=True)

        @dp.operator(op_name, terminal=True)
        class Done(Operator[bool]):  # pylint: disable=unused-variable
            """one and only op"""

            def can_perform(self, state: bool, _io: IOContainer) -> bool:
                return not state

            def perform(self, _state: bool, _io: IOContainer) -> bool:
                return True

        dp.run_until_done()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={True}",
                    f"Done?={True}",
                    f"Chosen={act_name}",
                    f"Action Factories={op_name}",
                    f"Potential Actions={act_name}",
                    "Action Evaluators=",
                    "Rankings=",
                    "Termination Checks=",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

    def test_terminal(self) -> None:
        """Confirming terminal check"""

        dp1: DecisionProcess[str] = DecisionProcess(
            stringify("start_blank")(lambda: ""), enable_terminal_check=False
        )

        dp2: DecisionProcess[str] = DecisionProcess(
            stringify("start_blank")(lambda: "")
        )

        do_regular = create_named_action(
            "do",
            lambda s, _io: "regular",
        )

        do_terminal = create_named_action(
            "do", lambda s, _io: "terminal", terminal=True
        )

        def allow_action(a: Action[str]) -> ActionFactory[str]:
            def can_do(_s: str, _io: IOContainer) -> Action[str]:
                return a

            return can_do

        dp1.add_action_factory(allow_action(do_regular)).run_cycles(100)

        self.assertFalse(dp1.done)

        (
            dp1.reinit()
            .add_action_factory(allow_action(do_terminal))
            .add_action_evaluator(uniform_evaluator(1))
            .run_cycles(100)
        )

        self.assertFalse(dp1.done)

        # ===

        dp2.add_action_factory(allow_action(do_regular)).run_cycles(100)

        self.assertFalse(dp2.done)

        dp2.add_action_factory(allow_action(do_terminal)).add_action_evaluator(
            uniform_evaluator(1)
        )

        for _ in range(100):
            dp2.reinit()
            self.assertEqual(dp2.state, "")

            dp2.run_cycles(100)
            self.assertTrue(dp2.done)
            self.assertEqual(dp2.state, "terminal")

    def test_operator(self) -> None:
        """Confirming operators"""

        hi_name: str = "hi"
        bye_name: str = "bye"
        done_name: str = "done_yet?"

        self.assertEqual(str(HiOp(hi_name)), f"HiOp({format_name_params(hi_name)})")
        self.assertEqual(
            str(HiOp(hi_name, foo="bar")),
            f"HiOp({format_name_params(hi_name, foo="bar")})",
        )

        dp: DecisionProcess[OpStage] = (
            DecisionProcess(stringify("start_hi")(lambda: OpStage.SAY_HI))
            .add_operator_c(HiOp(hi_name))
            .add_operator_c(ByeOp(bye_name))
        )

        @dp.termination_check
        @stringify(done_name)
        def check_done(s: OpStage, _io: IOContainer) -> bool:
            "done yet?"

            return s == OpStage.DONE

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={OpStage.SAY_HI}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    f"Action Factories={hi_name}, {bye_name}",
                    "Potential Actions=",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={done_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        dp.run_cycles()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={OpStage.SAY_BYE}",
                    f"Done?={False}",
                    f"Chosen={hi_name}",
                    f"Action Factories={hi_name}, {bye_name}",
                    f"Potential Actions={hi_name}",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={done_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertEqual(dp.log, "hi\n")

        dp.run_cycles()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={OpStage.DONE}",
                    f"Done?={False}",
                    f"Chosen={bye_name}",
                    f"Action Factories={hi_name}, {bye_name}",
                    f"Potential Actions={bye_name}",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={done_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertEqual(dp.log, "hi\nbye\n")

        dp.run_until_done()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={OpStage.DONE}",
                    f"Done?={True}",
                    f"Chosen={bye_name}",
                    f"Action Factories={hi_name}, {bye_name}",
                    f"Potential Actions={bye_name}",
                    "Action Evaluators=",
                    "Rankings=",
                    f"Termination Checks={done_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        self.assertEqual(dp.log, "hi\nbye\n")

    def test_named_action(self) -> None:
        """Confirming the named actions"""

        self.assertIsInstance(self.vote_yay, NamedObject)
        vote_yay_named = cast(NamedObject, self.vote_yay)

        name_yay = "vote"
        params_yay = {"value": "yay", "volume": 12}

        self.assertEqual(vote_yay_named.name, name_yay)

        self.assertEqual(vote_yay_named.params, params_yay)

        self.assertEqual(str(self.vote_yay), format_name_params(name_yay, **params_yay))

        self.assertEqual(self.vote_yay(42, self.mock_io), 1)

        # ===

        self.assertIsInstance(self.vote_nay, NamedObject)
        vote_nay_named = cast(NamedObject, self.vote_nay)

        name_nay = "vote"
        params_nay = {"value": "nay"}

        self.assertEqual(vote_nay_named.name, name_nay)

        self.assertEqual(vote_nay_named.params, params_nay)

        self.assertEqual(str(self.vote_nay), format_name_params(name_nay, **params_nay))

        self.assertEqual(self.vote_nay(42, self.mock_io), 0)

        # ===

        self.assertIsInstance(self.abstain, NamedObject)
        abstrain_named = cast(NamedObject, self.abstain)

        name_abstain = "abstain"
        params_abstain: dict[str, Any] = {}

        self.assertEqual(abstrain_named.name, name_abstain)

        self.assertEqual(abstrain_named.params, params_abstain)

        self.assertEqual(
            str(self.abstain), format_name_params(name_abstain, **params_abstain)
        )

        self.assertEqual(self.abstain(42, self.mock_io), -1)

    def test_uniform_evaluator(self) -> None:
        """Checks uniform_evaluator"""

        votes: list[Action[int]] = [self.vote_yay, self.vote_nay]
        candidates: list[Action[int]] = votes + [self.abstain]

        def is_vote(a: Action[int]) -> bool:
            """distinguishes actual votes"""
            return cast(NamedObject, a).name == "vote"

        name_all_m: str = "all_m"
        name_vote_h: str = "vote_h"

        eval_all_m: ActionEvaluator[int] = uniform_evaluator(
            Rank.MEDIUM, name=name_all_m
        )
        eval_all_m_nameless: ActionEvaluator[int] = uniform_evaluator(Rank.MEDIUM)
        eval_vote_h: ActionEvaluator[int] = uniform_evaluator(
            Rank.HIGH, is_vote, name_vote_h
        )

        self.assertEqual(str(eval_all_m), name_all_m)

        self.assertNotEqual(str(eval_all_m), str(eval_all_m_nameless))

        self.assertEqual(str(eval_vote_h), name_vote_h)

        # ===

        ranks = list(eval_all_m(51, self.mock_io, candidates))
        self.assertEqual(len(ranks), len(candidates))
        for c in candidates:
            self.assertIn(ActionRank(c, Rank.MEDIUM), ranks)

        ranks2 = list(eval_all_m_nameless(17, self.mock_io, candidates))
        self.assertEqual(ranks, ranks2)

        ranks = list(eval_vote_h(100, self.mock_io, candidates))
        self.assertEqual(len(ranks), len(votes))
        for c in votes:
            self.assertIn(ActionRank(c, Rank.HIGH), ranks)

        # HIGH < LOW b/c higher priority in sort
        self.assertTrue(ranks[0] < ranks2[0])

    def test_create_elaborator(self) -> None:
        """Checks create_elaborator"""

        name: str = "foo"

        elab: Elaborator[int] = create_elaborator(
            name,
            identity=lambda s, _: s,
            inc=lambda s, _: s + 1,
            neg=lambda s, _: -s,
        )

        # ===

        self.assertEqual(str(elab), name)

        self.assertEqual(
            elab(42, self.mock_io),
            {
                "identity": 42,
                "inc": 43,
                "neg": -42,
            },
        )

        self.assertEqual(
            elab(100, self.mock_io),
            {
                "identity": 100,
                "inc": 101,
                "neg": -100,
            },
        )

        # ===

        elab2: Elaborator[int] = create_elaborator(
            identity=lambda s, _: s,
            inc=lambda s, _: s + 1,
            neg=lambda s, _: -s,
        )

        self.assertNotEqual(str(elab), str(elab2))

        self.assertEqual(
            elab(42, self.mock_io),
            elab2(42, self.mock_io),
        )

        self.assertEqual(
            elab(100, self.mock_io),
            elab2(100, self.mock_io),
        )

    # pylint: disable=too-many-locals
    def test_sorting_evaluator(self) -> None:
        """Checks sorting_evaluator"""

        init_state: int = 3
        dp: DecisionProcess[int] = DecisionProcess(
            stringify("start_const")(lambda: init_state)
        )

        final_val: int = 10
        goal_name: str = f"at{final_val}"

        @dp.termination_check
        @stringify(goal_name)
        def atval(num: int, _io: IOContainer) -> bool:
            """achieved value!"""

            return num >= final_val

        add1 = ChangeOp(PrioritizedMathOperation.ADD, 1)
        add2 = ChangeOp(PrioritizedMathOperation.ADD, 2)
        sub1 = ChangeOp(PrioritizedMathOperation.SUB, 1)
        mult2 = ChangeOp(PrioritizedMathOperation.MULT, 2)
        mult2b = ChangeOp(PrioritizedMathOperation.MULT, 2)

        # confirming direct comparison
        self.assertTrue(add1 < add2)
        self.assertTrue(add1 < sub1)
        self.assertTrue(add1 < mult2)
        self.assertTrue(add2 < mult2)
        self.assertTrue(sub1 < mult2)
        self.assertTrue(mult2 == mult2b)

        # confirming tie-breaking
        op_param_tie: str = "foo"

        dp2: DecisionProcess[int] = DecisionProcess(stringify("start_42")(lambda: 42))
        _, a2, _ = dp2.add_operator(mult2, op_param_tie)
        _, a2b, _ = dp2.add_operator(mult2b, op_param_tie)

        evaluator: ActionEvaluator[int] = sorting_evaluator(
            operator_sorting_key(op_param_tie)
        )

        self.assertSequenceEqual(
            [ar.rank for ar in evaluator(dp2.state, self.mock_io, (a2, a2b))],
            (1, 1),
        )

        # proceed with real task
        ops: dict[ChangeOp, tuple[ActionFactory[int], Action[int]]] = {
            o: dp.add_operator(o)[:-1] for o in (add2, sub1, mult2, add1)
        }

        eval_name: str = "change_op_sort"
        rank_start: int = 100

        dp.add_action_evaluator(
            sorting_evaluator(
                operator_sorting_key(), rank_start=rank_start, name=eval_name
            )
        )

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state}",
                    f"Done?={False}",
                    f"Chosen={None}",
                    f"Action Factories={", ".join(o.name for o in ops)}",
                    "Potential Actions=",
                    f"Action Evaluators={eval_name}",
                    "Rankings=",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        # should increase by 1
        dp.run_cycles()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state + 1}",
                    f"Done?={False}",
                    f"Chosen={ops[add1][1] !s}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    f"Potential Actions={", ".join(str(ov[1]) for ov in ops.values())}",
                    f"Action Evaluators={eval_name}",
                    f"Rankings={
                    ", ".join(
                        str(ar)
                        for ar in (
                            ActionRank(ops[add1][1], rank_start),
                            ActionRank(ops[add2][1], rank_start+1),
                            ActionRank(ops[sub1][1], rank_start+2),
                            ActionRank(ops[mult2][1], rank_start+3),
                        )
                    )
                }",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        add1.flip()
        add2.flip()

        # should decrease by 1
        dp.run_cycles()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state}",
                    f"Done?={False}",
                    f"Chosen={ops[sub1][1] !s}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    (
                        "Potential Actions="
                        f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}"
                    ),
                    f"Action Evaluators={eval_name}",
                    f"Rankings={
                    ", ".join(
                        str(ar)
                        for ar in (
                            ActionRank(ops[sub1][1], rank_start),
                            ActionRank(ops[mult2][1], rank_start+1),
                        )
                    )
                }",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        sub1.flip()

        # should double
        dp.run_cycles()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state * 2}",
                    f"Done?={False}",
                    f"Chosen={ops[mult2][1] !s}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    (
                        "Potential Actions="
                        f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}"
                    ),
                    f"Action Evaluators={eval_name}",
                    "Rankings=",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

        add1.flip()
        add2.flip()

        dp.run_until_done()

        self.assertEqual(
            str(dp),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={final_val}",
                    f"Done?={True}",
                    f"Chosen={ops[add1][1] !s}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    (
                        "Potential Actions="
                        f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}"
                    ),
                    f"Action Evaluators={eval_name}",
                    f"Rankings={
                    ", ".join(
                        str(ar)
                        for ar in (
                            ActionRank(ops[add1][1], rank_start),
                            ActionRank(ops[add2][1], rank_start+1),
                            ActionRank(ops[mult2][1], rank_start+2),
                        )
                    )
                }",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Input Sources={BaseDecisionProcess.INPUT_KEY_TIME}",
                    f"Output Channels={BaseDecisionProcess.OUTPUT_KEY_LOG}",
                    "Elaborated Data=",
                    "Argument Values=",
                )
            ),
        )

    def test_generator(self) -> None:
        """testing generators"""

        letters = "DFTBA"
        syms = "!?$#"
        len_added = 10

        md_header = "# "

        # ===

        @dataclass(frozen=True)
        class SymLen:
            """combine symbol options and length constraint"""

            syms: str
            len_constraint: int

        # ===

        dp = DecisionProcess(stringify("start_blank")(lambda: ""))

        # arg gets negative character code (so reverse alpha)
        dp.add_action_evaluator(
            sorting_evaluator(
                lambda a, _s, _io: -ord(cast(NamedObject, a).params["s"]),
                lambda a: cast(NamedObject, a).name == "arg",
                rank_start=0,
            )
        )

        # done/emph use __lt__ and __eq__
        dp.add_action_evaluator(
            sorting_evaluator(
                operator_sorting_key(),
                lambda a: cast(NamedObject, a).name in ("done", "emph"),
                rank_start=10,
            )
        )

        # pylint: disable=unused-variable
        @dp.generator(None)
        class ArgGenerator(OperatorGenerator[str, None]):
            """aaarrrrrg"""

            def __init__(self, s: str) -> None:
                super().__init__(s=s)
                self.s = s

            @classmethod
            def get_name(cls) -> str:
                return "arg"

            @classmethod
            def generate(
                cls, state: str, io: IOContainer, _extra: None
            ) -> Iterable[Self]:
                yield from (cls(s) for s in io.a.incoming if s not in state)

            def perform(self, state: str, _io: IOContainer) -> str:
                return f"{state}{self.s}"

        class EmphGenerator(OperatorGenerator[str, SymLen]):
            """adds emphasis until a fixed len"""

            def __init__(self, sym: str) -> None:
                super().__init__(sym=sym)
                self.s = sym

            def perform(self, state: str, _io: IOContainer) -> str:
                return f"{state}{self.s}"

            @classmethod
            def get_name(cls) -> str:
                return "emph"

            @classmethod
            def generate(
                cls, state: str, _io: IOContainer, extra: SymLen
            ) -> Iterable[Self]:
                if len(state) >= extra.len_constraint:
                    yield from ()
                else:
                    for sym in extra.syms:
                        yield cls(sym)

            def __lt__(self, other: object) -> bool:
                """all emph comes before anything else"""

                if not isinstance(other, NamedObject):
                    return NotImplemented

                return self.name != other.name

            def __eq__(self, other: object) -> bool:
                """no pref amongst emph"""

                if not isinstance(other, NamedObject):
                    return NotImplemented

                return self.name == other.name

        # pylint: disable=unused-variable
        @dp.operator("done", terminal=True)
        class DoneOperator(Operator[str]):
            """gotta end sometime!"""

            def can_perform(self, _state: str, _io: IOContainer) -> bool:
                return True

            def perform(self, state: str, _io: IOContainer) -> str:
                return f"{md_header}{state}"

            def __lt__(self, other: object) -> bool:
                """done is always last"""

                return False

        dp.add_generator_c(EmphGenerator, SymLen(syms, len(set(letters)) + len_added))

        # ===

        result = dp(incoming=letters)
        exp_letters = "".join(sorted(set(letters), reverse=True))

        self.assertIsNotNone(result)
        result = cast(str, result)

        self.assertEqual(result[:2], md_header)
        result = result[2:]

        self.assertEqual(len(result), len(exp_letters) + len_added)

        self.assertEqual(result[: len(exp_letters)], exp_letters)

        for other in result[len(exp_letters) :]:
            self.assertTrue(other in syms)
