"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from __future__ import annotations

from collections.abc import Callable

from dataclasses import dataclass

from enum import IntEnum

from cognition import (
    AttrReferral,
    EnhancedTask,
    IOContainer,
    NamedOperator,
    Task,
    stringify,
)

from rich import print as rprint
from rich.prompt import Prompt

#

@dataclass(frozen=True)
class CommandLogEntry:
    """Logging past commands with result"""

    cmd: str
    result: CommandReturn

class CLIStage(IntEnum):
    """Step of CLI processing"""

    GET_CMD = 0
    EXEC_CMD = 1

    def next(self) -> CLIStage:
        """Next stage"""

        return CLIStage((self + 1) % len(CLIStage))

@dataclass
class CLIState:
    """
    Get/Process cmd
    +
    cmd log
    """

    stage: CLIStage
    log: list[CommandLogEntry]

#

# shared reference to
# command input buffer
cli_status: dict[str, str] = {}

#

@dataclass(frozen=True)
class CommandReturn:
    """CLI return: code and exit flag"""

    text: str
    code: int
    exit: bool

type Command = Callable[[], CommandReturn]

def register_command(dest: dict[str, Command]) -> Callable[[Command], Command]:
    """adds a command to the destination"""

    def dec(cmd: Command) -> Command:
        """actually registers the command"""

        dest[str(cmd)] = cmd
        return cmd

    return dec

#

commands: dict[str, Command] = {}

@register_command(commands)
@stringify("help")
def cmd_help() -> CommandReturn:
    """List of available commands"""

    return CommandReturn(
        f"Available commands: {", ".join(commands.keys())}",
        0,
        False
    )

@register_command(commands)
@stringify("hello")
def cmd_hello() -> CommandReturn:
    """Friendly!!"""

    return CommandReturn(":smile:", 0, False)

@register_command(commands)
@stringify("err")
def cmd_err() -> CommandReturn:
    """Badness"""

    return CommandReturn(
        ":scream: What we've got here is... failure to communicate",
        1,
        False
    )

@register_command(commands)
@stringify("bye")
def cmd_bye() -> CommandReturn:
    """Exit"""

    return CommandReturn(":waving_hand:", 0, True)

@register_command(commands)
@stringify("history")
def cmd_history() -> CommandReturn:
    """Log of past interactions"""

    return CommandReturn(
        "\n".join(
            str(entry) for entry in t.state.log
        ),
        0,
        False
    )

#

class GetCommand(NamedOperator[CLIState]):
    """GET_CMD -> $"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.GET_CMD

    def perform(self, state: CLIState, _io: IOContainer) -> None:
        cli_status["command"] = Prompt.ask("[bold blue]$[/]")
        state.stage = state.stage.next()


class ExecCommand(NamedOperator[CLIState]):
    """EXEC_CMD -> execute"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.EXEC_CMD

    def perform(self, state: CLIState, io: IOContainer) -> None:
        cmd = io.i.cli.command

        if cmd in commands:
            log_entry = CommandLogEntry(cmd, commands[cmd]())
        else:
            log_entry = CommandLogEntry(
                cmd,
                CommandReturn(f"Invalid command: {cmd}", 1, False)
            )

        state.log.append(log_entry)

        if log_entry.result.code != 0:
            rprint(f"[bold red]{log_entry.result.text}[/]")
        else:
            rprint(log_entry.result.text)
        print()

        state.stage = state.stage.next()


t: Task[CLIState] = (EnhancedTask(lambda: CLIState(CLIStage.GET_CMD, []))
    .add_operator_c(GetCommand("get_command"))
    .add_operator_c(ExecCommand("exec_command"))
    .set_sensor("cli", AttrReferral(cli_status))
)

@t.goal_check
def exit_flag(s: CLIState, _: IOContainer) -> bool:
    """Exit if told to!"""

    if s.log:
        return s.log[-1].result.exit

    return False

#

def main() -> None:
    """Start the CLI"""

    rprint("Welcome to SimpleCLI")
    rprint("Enter [code]help[/] to see available commands.")
    rprint()

    t.run_until_done()


if __name__ == "__main__":
    main()
