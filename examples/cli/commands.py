"""
Simple CLI command definitions
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Self

from cognition import stringify
from rich import print as rprint

# ===


@dataclass(frozen=True)
class CommandReturn:
    """CLI return: code and exit flag"""

    text: str
    code: int
    exit: bool

    def print(self) -> None:
        """result-dependent output"""

        if self.code != 0:
            rprint(f"[bold red]{self.text}[/]")
        else:
            rprint(self.text)
        print()

    @classmethod
    def invalid(cls, user_input: str) -> Self:
        """produce a log of an invalid command"""

        return cls(f"Invalid command: {user_input}", 1, False)


@dataclass(frozen=True)
class CommandLogEntry:
    """A past command with its result"""

    cmd: str
    result: CommandReturn

    @classmethod
    def attempt_exec(cls, user_input: str, log: Sequence[CommandLogEntry]) -> Self:
        """produce a log entry via a user input"""

        return cls(
            user_input,
            (
                CommandReturn.invalid(user_input)
                if user_input not in registered_commands
                else registered_commands[user_input](log)
            ),
        )


type Command = Callable[[Sequence[CommandLogEntry]], CommandReturn]
"""our commands take no arguments and produce text + code + exit flag"""


def register_command(dest: dict[str, Command]) -> Callable[[Command], Command]:
    """adds a command to the destination"""

    def dec(cmd: Command) -> Command:
        """actually registers the command"""

        dest[str(cmd)] = cmd
        return cmd

    return dec


# ===

registered_commands: dict[str, Command] = {}
"""registered as {str(cmd): callable}"""


@register_command(registered_commands)
@stringify("help")
def cmd_help(_log: Sequence[CommandLogEntry]) -> CommandReturn:
    """List of available commands"""

    return CommandReturn(
        f"Available commands: {", ".join(registered_commands.keys())}", 0, False
    )


@register_command(registered_commands)
@stringify("hello")
def cmd_hello(_log: Sequence[CommandLogEntry]) -> CommandReturn:
    """Friendly!!"""

    return CommandReturn(":smile:", 0, False)


@register_command(registered_commands)
@stringify("err")
def cmd_err(_log: Sequence[CommandLogEntry]) -> CommandReturn:
    """Badness"""

    return CommandReturn(
        ":scream: What we've got here is... failure to communicate", 1, False
    )


@register_command(registered_commands)
@stringify("bye")
def cmd_bye(_log: Sequence[CommandLogEntry]) -> CommandReturn:
    """Exit"""

    return CommandReturn(":waving_hand:", 0, True)


@register_command(registered_commands)
@stringify("history")
def cmd_history(log: Sequence[CommandLogEntry]) -> CommandReturn:
    """Log of past interactions"""

    return CommandReturn("\n".join(str(entry) for entry in log), 0, False)
