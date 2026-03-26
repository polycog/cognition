"""
Tests for convenience code
"""

from typing import cast

import unittest

from cognition import (
    Action,
    ActionEvaluator,
    ActionRank,
    AttrReferral,
    Elaborator,
    IOContainer,
    NamedAction,
    Rank,
    create_named_action,
    create_elaborator,
    uniform_evaluator,
)

#

class TestConvenience(unittest.TestCase):
    """Tests for convenience code"""

    def setUp(self):
        self.vote_yay = create_named_action(
            "vote",
            lambda s, _io: s,
            value="yay",
            volume=12
        )

        self.vote_nay = create_named_action(
            "vote",
            lambda s, _io: s,
            value="nay",
        )

        self.abstain = create_named_action(
            "abstain",
            lambda _s, _io: None
        )

        self.io_source = {}
        self.mock_io = IOContainer(
            AttrReferral(self.io_source),
            AttrReferral(self.io_source)
        )


    def test_named_action(self) -> None:
        """Confirming the named actions"""

        self.assertIsInstance(self.vote_yay, NamedAction)

        self.assertEqual(
            self.vote_yay.name,
            "vote"
        )

        self.assertEqual(
            self.vote_yay.params,
            {
                "value": "yay",
                "volume": 12
            }
        )

        self.assertEqual(
            str(self.vote_yay),
            "vote[value='yay', volume=12]"
        )

        self.assertEqual(
            self.vote_yay("a", self.mock_io),
            "a"
        )

        #

        self.assertIsInstance(self.vote_nay, NamedAction)

        self.assertEqual(
            self.vote_nay.name,
            "vote"
        )

        self.assertEqual(
            self.vote_nay.params,
            {"value": "nay"}
        )

        self.assertEqual(
            str(self.vote_nay),
            "vote[value='nay']"
        )

        self.assertEqual(
            self.vote_nay(42, self.mock_io),
            42
        )

        #

        self.assertIsInstance(self.abstain, NamedAction)

        self.assertEqual(
            self.abstain.name,
            "abstain"
        )

        self.assertEqual(
            self.abstain.params,
            {}
        )

        self.assertEqual(
            str(self.abstain),
            "abstain"
        )

        self.assertIsNone(
            self.abstain(3.14, self.mock_io)
        )


    def test_uniform_evaluator(self) -> None:
        """Checks uniform_evaluator"""

        votes: list[Action] = [self.vote_yay, self.vote_nay]
        candidates: list[Action] = votes + [self.abstain]

        def is_vote(a: Action) -> bool:
            """distinguishes actual votes"""
            return cast(NamedAction, a).name == "vote"

        name_all_m: str = "all_m"
        name_vote_h: str = "vote_h"

        eval_all_m: ActionEvaluator = uniform_evaluator(Rank.MEDIUM, name=name_all_m)
        eval_all_m_nameless: ActionEvaluator = uniform_evaluator(Rank.MEDIUM)
        eval_vote_h: ActionEvaluator = uniform_evaluator(Rank.HIGH, is_vote, name_vote_h)

        self.assertEqual(
            str(eval_all_m),
            name_all_m
        )

        self.assertNotEqual(
            str(eval_all_m),
            str(eval_all_m_nameless)
        )

        self.assertEqual(
            str(eval_vote_h),
            name_vote_h
        )

        #

        ranks = list(eval_all_m(None, self.mock_io, candidates))
        self.assertEqual(len(ranks), len(candidates))
        for c in candidates:
            self.assertIn(
                ActionRank(
                    c,
                    Rank.MEDIUM
                ),
                ranks
            )

        ranks2 = list(eval_all_m_nameless(None, self.mock_io, candidates))
        self.assertEqual(ranks, ranks2)


        ranks = list(eval_vote_h(self.io_source, self.mock_io, candidates))
        self.assertEqual(len(ranks), len(votes))
        for c in votes:
            self.assertIn(
                ActionRank(
                    c,
                    Rank.HIGH
                ),
                ranks
            )

        # HIGH < LOW b/c higher priority in sort
        self.assertTrue(
            ranks[0] < ranks2[0]
        )

    def test_create_elaborator(self) -> None:
        """Checks create_elaborator"""

        name: str = "foo"

        elab: Elaborator[int] = create_elaborator(
            name,
            identity = lambda s, _: s,
            inc = lambda s, _: s + 1,
            neg = lambda s, _: -s,
        )

        #

        self.assertEqual(
            str(elab),
            name
        )

        self.assertEqual(
            elab(42, self.mock_io),
            {
                "identity": 42,
                "inc": 43,
                "neg": -42,
            }
        )

        self.assertEqual(
            elab(100, self.mock_io),
            {
                "identity": 100,
                "inc": 101,
                "neg": -100,
            }
        )

        #

        elab2: Elaborator[int] = create_elaborator(
            identity = lambda s, _: s,
            inc = lambda s, _: s + 1,
            neg = lambda s, _: -s,
        )

        self.assertNotEqual(
            str(elab),
            str(elab2)
        )

        self.assertEqual(
            elab(42, self.mock_io),
            elab2(42, self.mock_io),
        )

        self.assertEqual(
            elab(100, self.mock_io),
            elab2(100, self.mock_io),
        )
