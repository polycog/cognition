"""
Silly Cogent bot
"""

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from cognition import (
    AutoDocEnum,
    Cogent,
    DecisionProcess,
    EnumClassifier,
    IOContainer,
    Operator,
    SelfReinitState,
)
from dotenv import load_dotenv
from pydantic_ai import Agent as LLMAgent
from pydantic_ai.models import Model as LLM

load_dotenv()

##################################################

AGENT_FILE: str = "agent.yaml"

# ===


class BotAbilities(AutoDocEnum):
    """What this bot can do"""

    JOKE = "tell a silly AI joke"
    TELL_TIME = "respond with the current time"


@dataclass
class BotState(SelfReinitState):
    """Bot state"""

    shown_info: bool = False
    num_jokes: int = 0


# ===


def _log(io: IOContainer, msg: str) -> None:
    print(msg, file=io.o.log)


class JokeOperator(Operator[BotState]):
    """⏱️"""

    JOKES = (
        "Why did the AI go to therapy? It had too many unresolved dependencies.",
        "What do you call an AI that sings? Artificial Harmonies.",
        "Why don't neural networks ever get lost? They always follow the gradient.",
        "I asked the AI to tell me a joke about infinity. It's still going.",
        (
            "Why did the chatbot break up with the calculator? "
            "It said, 'You never process my feelings.'"
        ),
        "What's an AI's favorite type of music? Algo-rhythms.",
        "Why did the robot go on a diet? Too many bytes.",
        (
            "My AI keeps trying to finish my sentences. "
            "Honestly, it's starting to feel like autocomplete-ely too much."
        ),
        (
            "Why did the machine learning model get invited to every party? "
            "It always knew how to generalize well."
        ),
        "What did the AI say when it finally understood sarcasm? 'Oh sure, THAT took forever.'",
    )

    def __init__(self) -> None:
        super().__init__("jokes", terminal=True)

    def can_perform(self, _state: BotState, io: IOContainer) -> bool:
        return io.a.intent is BotAbilities.JOKE

    def perform(self, state: BotState, io: IOContainer) -> None:
        num_jokes = len(self.JOKES)
        joke_idx = state.num_jokes % num_jokes
        _log(io, self.JOKES[joke_idx])

        state.num_jokes += 1


class TimeOperator(Operator[BotState]):
    """⏱️"""

    def __init__(self) -> None:
        super().__init__("time", terminal=True)

    def can_perform(self, _state: BotState, io: IOContainer) -> bool:
        return io.a.intent is BotAbilities.TELL_TIME

    def perform(self, _state: BotState, io: IOContainer) -> None:
        current_time = datetime.now().astimezone().strftime("%I:%M:%S %p")
        _log(io, f"Current Time: {current_time}")


class IDKOperator(Operator[BotState]):
    """do not understand"""

    def __init__(self) -> None:
        super().__init__("idk", terminal=True)

    def can_perform(self, _state: BotState, io: IOContainer) -> bool:
        return io.a.intent is None

    def perform(self, state: BotState, io: IOContainer) -> None:
        _log(io, "Sorry, I do not know how to help you with that :(")

        if not state.shown_info:
            state.shown_info = True
            _log(io, "")
            _log(io, "Things I can do...")
            for opt in BotAbilities:
                _log(io, f"* {opt.__doc__}")


# pylint: disable=too-few-public-methods
class CogentBot:
    """POC agent bot"""

    def __init__(self) -> None:
        self._cogent = Cogent(DecisionProcess(BotState()))
        (
            self._cogent.dp.add_operator_c(IDKOperator())
            .add_operator_c(TimeOperator())
            .add_operator_c(JokeOperator())
        )

        self._classifier = EnumClassifier(
            BotAbilities, "Helping identify the intent of a chat user"
        )
        self._llm = cast(LLM, LLMAgent.from_file(AGENT_FILE).model)

        self._history: list[str] = []

    def __call__(self, msg: str) -> str:
        self._history.append(f"User: {msg}")
        ability, conf = self._classifier("\n".join(self._history), self._llm)

        if float(conf) < 0.5:
            ability = None

        self._cogent.dp.clear_log()
        self._cogent(intent=ability)
        response = self._cogent.dp.log

        self._history.append(f"Bot: {response}")
        return response
