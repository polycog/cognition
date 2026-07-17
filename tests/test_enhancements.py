"""
Tests for enhancement code
"""

from typing import (
    Any,
    cast,
)

from enum import Enum, StrEnum, auto

from collections.abc import Mapping

import unittest

from cognition import (
    Action,
    ActionEvaluator,
    ActionFactory,
    ActionRank,
    AttrReferral,
    BiFunction,
    Elaborator,
    EnhancedTask,
    IOContainer,
    NamedAction,
    Operator,
    Phase,
    Rank,
    Task,
    args_added,
    create_named_action,
    create_elaborator,
    operator_sorting_key,
    sorting_evaluator,
    stringify,
    uniform_evaluator,
)

#


class OpStage(StrEnum):
    """Stage of op test"""

    SAY_HI = auto()
    SAY_BYE = auto()
    DONE = auto()


class HiOp(Operator[OpStage]):
    """Says hi"""

    def can_perform(self, state: OpStage, io: IOContainer) -> bool:
        return state == OpStage.SAY_HI

    def perform(self, state: OpStage, io: IOContainer) -> OpStage:
        print("hi", file=io.o.log)
        return OpStage.SAY_BYE


class ByeOp(Operator[OpStage]):
    """Says bye"""

    def can_perform(self, state: OpStage, io: IOContainer) -> bool:
        return state == OpStage.SAY_BYE

    def perform(self, state: OpStage, io: IOContainer) -> OpStage:
        print("bye", file=io.o.log)
        return OpStage.DONE


#


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


#


class TestEnhancements(unittest.TestCase):
    """Tests for enhancement code"""

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
            AttrReferral(self.io_source), AttrReferral(self.io_source)
        )

    def test_args_call(self) -> None:
        """Confirming arguments context manager with __call__"""

        state_start = 0

        t = EnhancedTask(lambda: state_start, enable_terminal_check=True)

        self.assertEqual(t.state, state_start)

        #

        namespace = "foo"
        arg_name = "bar"
        arg_val = 42

        # pylint: disable=unused-variable
        @t.operator("copy", terminal=True, arg_name=arg_name)
        class ArgCopy(Operator[int]):
            """Copies the arg"""

            def __init__(self, name: str, arg_name: str, **kwargs: Any) -> None:
                super().__init__(name, **kwargs)
                self._arg = arg_name

            def can_perform(self, _state: int, _io: IOContainer) -> bool:
                return True

            def perform(self, _state: int, io: IOContainer) -> int:
                args = getattr(io.i, namespace)
                return cast(int, getattr(args, self._arg))

        with args_added(t, namespace=namespace, **{arg_name: arg_val}):
            t.run_until_done()

        self.assertTrue(t.done)
        self.assertEqual(t.state, arg_val)

        #

        t.reinit()

        self.assertEqual(t.state, state_start)
        self.assertEqual(
            t(
                max_cycles=2,
                suppress_errors=True,
                args_namespace=namespace,
                **{arg_name: arg_val},
            ),
            arg_val,
        )

        t.reinit()

        self.assertEqual(t.state, state_start)
        self.assertIsNone(
            t(
                max_cycles=0,
                suppress_errors=True,
                args_namespace=namespace,
                **{arg_name: arg_val},
            ),
            arg_val,
        )
        self.assertFalse(t.done)

        t.reinit()
        self.assertEqual(t.state, state_start)
        self.assertIsNone(t())
        self.assertFalse(t.done)

        t.reinit()
        self.assertEqual(t.state, state_start)
        with self.assertRaises(RuntimeError):
            self.assertIsNone(t(suppress_errors=False))

    def test_named_op_decorator(self) -> None:
        """Confirming named operator decorator"""

        t: EnhancedTask[bool] = EnhancedTask(lambda: False, enable_terminal_check=True)

        op_name = "done"
        act_name = f"{op_name}[terminal=True]"

        @t.operator(op_name, terminal=True)
        class Done(Operator[bool]):  # pylint: disable=unused-variable
            """one and only op"""

            def can_perform(self, state: bool, _io: IOContainer) -> bool:
                return not state

            def perform(self, _state: bool, _io: IOContainer) -> bool:
                return True

        t.run_until_done()

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

    def test_terminal(self) -> None:
        """Confirming terminal check"""

        t1: EnhancedTask[str] = EnhancedTask(
            lambda: "",
        )

        t2: EnhancedTask[str] = EnhancedTask(lambda: "", enable_terminal_check=True)

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

        t1.add_action_factory(allow_action(do_regular)).run_cycles(100)

        self.assertFalse(t1.done)

        (
            t1.reinit()
            .add_action_factory(allow_action(do_terminal))
            .add_action_evaluator(uniform_evaluator(1))
            .run_cycles(100)
        )

        self.assertFalse(t1.done)

        #

        t2.add_action_factory(allow_action(do_regular)).run_cycles(100)

        self.assertFalse(t2.done)

        t2.add_action_factory(allow_action(do_terminal)).add_action_evaluator(
            uniform_evaluator(1)
        )

        for _ in range(100):
            t2.reinit()
            self.assertEqual(t2.state, "")

            t2.run_cycles(100)
            self.assertTrue(t2.done)
            self.assertEqual(t2.state, "terminal")

    def test_operator(self) -> None:
        """Confirming operators"""

        hi_name: str = "hi"
        bye_name: str = "bye"
        done_name: str = "done_yet?"

        t: EnhancedTask[OpStage] = (
            EnhancedTask(lambda: OpStage.SAY_HI)
            .add_operator_c(HiOp(hi_name))
            .add_operator_c(ByeOp(bye_name))
        )

        @t.termination_check
        @stringify(done_name)
        def check_done(s: OpStage, _io: IOContainer) -> bool:
            "done yet?"

            return s == OpStage.DONE

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        t.run_cycles()

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        self.assertEqual(t.log, "hi\n")

        t.run_cycles()

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        self.assertEqual(t.log, "hi\nbye\n")

        t.run_until_done()

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        self.assertEqual(t.log, "hi\nbye\n")

    def test_named_action(self) -> None:
        """Confirming the named actions"""

        self.assertIsInstance(self.vote_yay, NamedAction)
        vote_yay_named = cast(NamedAction, self.vote_yay)

        self.assertEqual(vote_yay_named.name, "vote")

        self.assertEqual(vote_yay_named.params, {"value": "yay", "volume": 12})

        self.assertEqual(str(self.vote_yay), "vote[value='yay', volume=12]")

        self.assertEqual(self.vote_yay(42, self.mock_io), 1)

        #

        self.assertIsInstance(self.vote_nay, NamedAction)
        vote_nay_named = cast(NamedAction, self.vote_nay)

        self.assertEqual(vote_nay_named.name, "vote")

        self.assertEqual(vote_nay_named.params, {"value": "nay"})

        self.assertEqual(str(self.vote_nay), "vote[value='nay']")

        self.assertEqual(self.vote_nay(42, self.mock_io), 0)

        #

        self.assertIsInstance(self.abstain, NamedAction)
        abstrain_named = cast(NamedAction, self.abstain)

        self.assertEqual(abstrain_named.name, "abstain")

        self.assertEqual(abstrain_named.params, {})

        self.assertEqual(str(self.abstain), "abstain")

        self.assertEqual(self.abstain(42, self.mock_io), -1)

    def test_uniform_evaluator(self) -> None:
        """Checks uniform_evaluator"""

        votes: list[Action[int]] = [self.vote_yay, self.vote_nay]
        candidates: list[Action[int]] = votes + [self.abstain]

        def is_vote(a: Action[int]) -> bool:
            """distinguishes actual votes"""
            return cast(NamedAction, a).name == "vote"

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

        #

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

        #

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

        #

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
        t: EnhancedTask[int] = EnhancedTask(lambda: init_state)

        final_val: int = 10
        goal_name: str = f"at{final_val}"

        @t.termination_check
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

        t2: EnhancedTask[int] = EnhancedTask(lambda: 42)
        _, a2, _ = t2.add_operator(mult2, op_param_tie)
        _, a2b, _ = t2.add_operator(mult2b, op_param_tie)

        evaluator: ActionEvaluator[int] = sorting_evaluator(
            operator_sorting_key(op_param_tie)
        )

        self.assertSequenceEqual(
            list(ar.rank for ar in evaluator(t2.state, self.mock_io, (a2, a2b))), (1, 1)
        )

        # proceed with real task
        ops: dict[ChangeOp, tuple[ActionFactory[int], Action[int]]] = {
            o: t.add_operator(o)[:-1] for o in (add2, sub1, mult2, add1)
        }

        eval_name: str = "change_op_sort"
        rank_start: int = 100

        t.add_action_evaluator(
            sorting_evaluator(
                operator_sorting_key(), rank_start=rank_start, name=eval_name
            )
        )

        self.assertEqual(
            str(t),
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        # should increase by 1
        t.run_cycles()

        self.assertEqual(
            str(t),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state + 1}",
                    f"Done?={False}",
                    f"Chosen={str(ops[add1][1])}",
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        add1.flip()
        add2.flip()

        # should decrease by 1
        t.run_cycles()

        self.assertEqual(
            str(t),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state}",
                    f"Done?={False}",
                    f"Chosen={str(ops[sub1][1])}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    "Potential Actions="
                    f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}",
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        sub1.flip()

        # should double
        t.run_cycles()

        self.assertEqual(
            str(t),
            "\n".join(
                (
                    f"Phase={Phase.ELABORATION.name}",
                    f"State={init_state * 2}",
                    f"Done?={False}",
                    f"Chosen={str(ops[mult2][1])}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    "Potential Actions="
                    f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}",
                    f"Action Evaluators={eval_name}",
                    "Rankings=",
                    f"Termination Checks={goal_name}",
                    "Elaborators=",
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )

        add1.flip()
        add2.flip()

        t.run_until_done()

        self.assertEqual(
            str(t),
            "\n".join(
                (
                    f"Phase={Phase.TERMINATIONCHECK.name}",
                    f"State={final_val}",
                    f"Done?={True}",
                    f"Chosen={str(ops[add1][1])}",
                    f"Action Factories={", ".join(str(ov[0]) for ov in ops.values())}",
                    "Potential Actions="
                    f"{", ".join(str(ov[1]) for o,ov in ops.items() if o.enabled)}",
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
                    f"Sensors={Task.SENSOR_TIME}, {Task.SENSOR_ELABORATION}",
                    f"Actuators={Task.ACTUATOR_LOG}",
                )
            ),
        )
