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
    IOContainer,
    NamedAction,
    Rank,
    uniform_evaluator,
)

#

class TestConvenience(unittest.TestCase):
    """Tests for convenience code"""

    def setUp(self):
        self.vote_yay = NamedAction("vote", lambda s, _io: s, value="yay", volume=12)
        self.vote_nay = NamedAction("vote", lambda s, _io: s, value="nay")
        self.abstain = NamedAction("abstain", lambda _s, _io: None)

        self.io_source = {}
        self.mock_io = IOContainer(
            AttrReferral(self.io_source),
            AttrReferral(self.io_source)
        )

    def test_named_action(self) -> None:
        """Confirming the named actions"""

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

        eval_all_m: ActionEvaluator = uniform_evaluator(Rank.MEDIUM)
        eval_yay_h: ActionEvaluator = uniform_evaluator(Rank.HIGH, is_vote)

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


        ranks = list(eval_yay_h(self.io_source, self.mock_io, candidates))
        self.assertEqual(len(ranks), len(votes))
        for c in votes:
            self.assertIn(
                ActionRank(
                    c,
                    Rank.HIGH
                ),
                ranks
            )
