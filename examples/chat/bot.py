"""
Chat bot definitions
"""

from multiprocessing.queues import Queue as MPQueue
from typing import Self, cast

from cognition import Function, Supplier

from data import Message, MessageType

# ===

type BotFactory = Supplier[Function[str, str]]
"""worker needs something created that can respond to incoming messages"""


def bot_worker(
    in_queue: MPQueue[Message], out_queue: MPQueue[Message], bot_factory: BotFactory
) -> None:
    """Responds to each message"""

    responder = bot_factory()

    while True:
        in_msg = in_queue.get()

        if in_msg.type == MessageType.EXIT:
            break

        out_queue.put(Message(MessageType.INFO, responder(cast(str, in_msg.content))))

    out_queue.put(Message(MessageType.EXIT, None))


# ===


# pylint: disable=too-few-public-methods
class EchoBot:
    """POC bot"""

    @classmethod
    def create_excited(cls) -> Self:
        """supplier of excited echo"""

        return cls(2)

    def __init__(self, excitement_level: int = 0) -> None:
        self._n = max(excitement_level, 0)

    def __call__(self, msg: str) -> str:
        return f"{msg}{self._n * "!"}"
