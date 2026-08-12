"""
Example of a simple chatbot
"""

import argparse
import logging
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as MPQueue
from pathlib import Path

from cognition import AutoDocEnum, EnumDispatch
from textual_serve.server import Server

from bot import bot_worker
from chat import ChatApp
from cogent import CogentBot
from data import Message

# ===

handler = logging.FileHandler("_log.txt", encoding="UTF-8")
handler.setFormatter(
    logging.Formatter(
        fmt="%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(handler)

cognition_logger = logging.getLogger("cognition")
cognition_logger.setLevel(logging.INFO)
cognition_logger.addHandler(handler)

# ===


class ChatView(AutoDocEnum):
    """
    Chat view choice
    """

    TUI = "local tui"
    WEB = "tui via browser"


class ChatDispatch(EnumDispatch[ChatView]):
    """
    Dispatch chat app ala view
    """

    def __init__(self, public_web_url: str | None = None) -> None:
        self._pub_web_url = public_web_url

    def tui(self) -> None:
        """local tui"""

        in_q: MPQueue[Message] = Queue()
        out_q: MPQueue[Message] = Queue()

        # ===

        # bot_factory = EchoBot # simple example (requires import from bot)
        # bot_factory = EchoBot.create_excited # simple example (requires import from bot)
        bot_factory = CogentBot

        _logger.debug("tui: queues and responder ready")

        # ===

        p_bot = Process(
            target=bot_worker, args=(in_q, out_q, bot_factory)
        )
        _logger.debug("tui: bot process ready")

        interface = ChatApp(in_q, out_q)
        _logger.debug("tui: interface ready")

        p_bot.start()
        _logger.debug("tui: bot process started")

        interface.run()
        _logger.debug("tui: interface done")

        p_bot.join()
        _logger.debug("tui: bot process done")

    def web(self) -> None:
        """browser-based tui"""

        f_name = Path(__file__).name

        Server(command=f"python {f_name}", public_url=self._pub_web_url).serve()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Chat")

    parser.add_argument(
        "--view",
        choices=[v.name for v in list(ChatView)],
        default=ChatView.TUI.name,
        help="App view",
    )

    parser.add_argument("--url", default="", help="Public URL (for web view)")

    args = parser.parse_args()

    chat_view = ChatView[args.view]
    pub_url = None if not args.url.strip() else args.url

    # ===

    ChatDispatch(pub_url).dispatch(chat_view)
