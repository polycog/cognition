"""
Chat TUI
"""

from multiprocessing.queues import Queue as MPQueue

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input, Static

from data import MESSAGE_EXIT, Message, MessageType

# ===

EXIT_TEXT = "exit"
"""Indication to exit"""


class ChatApp(App[None]):
    """
    Textual chat application
    """

    TITLE = "Chat"
    SUB_TITLE = "A PoC Interface"

    AUTO_FOCUS = "Input"

    CSS = """
    #chat-box {
        height: 1fr;
        border: $panel;
        margin: 1;
        padding: 1;
    }
    Input {
        dock: bottom;
        margin: 1;
    }
    .user-msg {
        background: $surface;
        margin: 1 0;
        padding: 0 1;
    }
    .bot-msg {
        background: $surface;
        color: $accent;
        margin: 1 0;
        padding: 0 1;
    }
    """

    def __init__(self, post_q: MPQueue[Message], get_q: MPQueue[Message]) -> None:
        super().__init__()

        self._post_q = post_q
        self._get_q = get_q

    def on_mount(self) -> None:
        """Called when the app is ready"""

        self.theme = "dracula"
        self.handle_results()

    def on_unmount(self) -> None:
        """Called when app is closing"""

        self._post_q.put(MESSAGE_EXIT)

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="chat-box"):
            yield Static(
                "Welcome to the Chat! Type a message below.", classes="bot-msg"
            )
        yield Input(
            placeholder=f"Type your message here (or {EXIT_TEXT} to end)...",
            id="user-input",
        )
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event: input box submitted"""

        entered = event.value.strip()
        if not entered:
            return

        chat_box = self.query_one("#chat-box", VerticalScroll)
        chat_box.mount(Static(f"You: {entered}", classes="user-msg"))

        if entered.lower() == EXIT_TEXT:
            out_msg = MESSAGE_EXIT
        else:
            out_msg = Message(MessageType.INFO, entered)

        self._post_q.put(out_msg)

        self.query_one("#user-input", Input).value = ""
        chat_box.scroll_end(animate=False)

        if out_msg.type == MessageType.EXIT:
            self.exit()

    @work(thread=True)
    def handle_results(self) -> None:
        """Ongoing: processing incoming message queue"""

        while True:
            in_msg: Message = self._get_q.get()

            if in_msg.type == MessageType.EXIT:
                break

            chat_box = self.query_one("#chat-box", VerticalScroll)

            self.call_from_thread(
                chat_box.mount,  # type: ignore
                Static(f"Result: {in_msg.content}", classes="bot-msg"),
            )

            self.call_from_thread(chat_box.scroll_end, animate=False)
