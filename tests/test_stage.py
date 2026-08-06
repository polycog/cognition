"""
Tests for stage code
"""

import unittest
from dataclasses import dataclass
from io import StringIO
from unittest.mock import MagicMock, patch

from cognition import (
    AutoDocEnum,
    DecisionProcess,
    IOContainer,
    KWArgs,
    StagedState,
    staged_operator,
    stringify,
)

# ===


class AuthStage(AutoDocEnum):
    """stage of authenticating"""

    INIT = "initialization"
    ATTEMPT = "try a pw"
    IN = "success"
    ALARM = "too many attempts"


@dataclass
class AuthState(StagedState[AuthStage]):
    """full authentication state"""

    stage: AuthStage = AuthStage.INIT
    attempts: int = 0

    def init(self) -> AuthStage:
        """transition to... attempt"""

        return AuthStage.ATTEMPT

    def attempt(self, correct_pw: bool, max_attempts: int) -> AuthStage:
        """attempt was made!"""

        self.attempts += 1

        if correct_pw:
            return AuthStage.IN

        if self.attempts < max_attempts:
            return AuthStage.ATTEMPT

        return AuthStage.ALARM


class TestStage(unittest.TestCase):
    """Tests for stage code"""

    def setUp(self) -> None:
        self.dp = DecisionProcess(AuthState)

        @staged_operator(self.dp, AuthStage.INIT)
        @stringify("perform_init")
        def _perform_init(_s: AuthState, io: IOContainer) -> None:
            print("Howdy!!")
            print(
                f"Please provide the secret within {io.i.args.max_attempts} attempt(s)."
            )
            print()

        @staged_operator(self.dp, AuthStage.ATTEMPT)
        @stringify("perform_attempt")
        def _perform_attempt(_s: AuthState, io: IOContainer) -> KWArgs:
            return {
                "correct_pw": input("Enter password: ") == io.i.args.secret,
                "max_attempts": io.i.args.max_attempts,
            }

        @staged_operator(self.dp, AuthStage.IN, terminal=True)
        @stringify("perform_in")
        def _perform_in(_s: AuthState, _io: IOContainer) -> None:
            print("Welcome!")

        @staged_operator(self.dp, AuthStage.ALARM, terminal=True)
        @stringify("perform_alarm")
        def _perform_alarm(s: AuthState, _io: IOContainer) -> None:
            print(f"Invalid after {s.attempts} attempt(s)!")

    @patch("builtins.input", side_effect=["polycog", "password", "1234", "abcdefg"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_stage_auth_good_1st(
        self, mock_stdout: StringIO, _mock_input: MagicMock
    ) -> None:
        """
        test staged decision process
        """

        num_attempts: int = 3
        secret: str = "polycog"

        self.dp(max_attempts=num_attempts, secret=secret)

        self.assertEqual(self.dp.state.stage, AuthStage.IN)
        self.assertEqual(self.dp.state.attempts, 1)

        self.assertEqual(
            mock_stdout.getvalue(),
            "\n".join(
                (
                    "Howdy!!",
                    f"Please provide the secret within {num_attempts} attempt(s).",
                    "",
                    "Welcome!",
                    "",
                )
            ),
        )

    @patch("builtins.input", side_effect=["password", "1234", "polycog", "abcdefg"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_stage_auth_good_3rd(
        self, mock_stdout: StringIO, _mock_input: MagicMock
    ) -> None:
        """
        test staged task
        """

        num_attempts: int = 3
        secret: str = "polycog"

        self.dp(max_attempts=num_attempts, secret=secret)

        self.assertEqual(self.dp.state.stage, AuthStage.IN)
        self.assertEqual(self.dp.state.attempts, 3)

        self.assertEqual(
            mock_stdout.getvalue(),
            "\n".join(
                (
                    "Howdy!!",
                    f"Please provide the secret within {num_attempts} attempt(s).",
                    "",
                    "Welcome!",
                    "",
                )
            ),
        )

    @patch("builtins.input", side_effect=["password", "1234", "polycog", "abcdefg"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_stage_auth_bad(
        self, mock_stdout: StringIO, _mock_input: MagicMock
    ) -> None:
        """
        test staged task
        """

        num_attempts: int = 2
        secret: str = "polycog"

        self.dp(max_attempts=num_attempts, secret=secret)

        self.assertEqual(self.dp.state.stage, AuthStage.ALARM)
        self.assertEqual(self.dp.state.attempts, 2)

        self.assertEqual(
            mock_stdout.getvalue(),
            "\n".join(
                (
                    "Howdy!!",
                    f"Please provide the secret within {num_attempts} attempt(s).",
                    "",
                    f"Invalid after {num_attempts} attempt(s)!",
                    "",
                )
            ),
        )
