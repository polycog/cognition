"""
Common data definitions
"""

from dataclasses import dataclass

from cognition import AutoDocEnum

# ===


class MessageType(AutoDocEnum):
    """
    Message type flag
    """

    INFO = "informational"
    EXIT = "exit the app"


@dataclass(frozen=True)
class Message:
    """Message"""

    type: MessageType
    content: str | None


MESSAGE_EXIT = Message(MessageType.EXIT, None)
