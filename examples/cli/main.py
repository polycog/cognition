"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from __future__ import annotations

from collections.abc import Callable

from dataclasses import dataclass

from cognition import (
    AttrReferral,
    AutoDocEnum,
    EnhancedTask,
    IOContainer,
    NamedOperator,
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


class CLIStage(AutoDocEnum):
    """Step of CLI processing"""

    GET_CMD = "get the command"
    EXEC_CMD = "execute the command"


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

    return CommandReturn(f"Available commands: {", ".join(commands.keys())}", 0, False)


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
        ":scream: What we've got here is... failure to communicate", 1, False
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

    return CommandReturn("\n".join(str(entry) for entry in t.state.log), 0, False)


#

# shared reference across IO
_cli_status: dict[str, str] = {}

t = (
    EnhancedTask(lambda: CLIState(CLIStage.GET_CMD, []))
    .set_sensor("cli", AttrReferral(_cli_status))
    .set_actuator("cli_set_command", lambda c: _cli_status.update(command=c))
)


@t.operator("get_command")
class GetCommand(NamedOperator[CLIState]):
    """GET_CMD -> $"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.GET_CMD

    def perform(self, state: CLIState, io: IOContainer) -> None:
        io.o.cli_set_command(Prompt.ask(f"[bold blue]{ io.i.args.shell_sym }[/]"))

        state.stage = CLIStage.EXEC_CMD


@t.operator("exec_command")
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
                cmd, CommandReturn(f"Invalid command: {cmd}", 1, False)
            )

        state.log.append(log_entry)

        if log_entry.result.code != 0:
            rprint(f"[bold red]{log_entry.result.text}[/]")
        else:
            rprint(log_entry.result.text)
        print()

        state.stage = CLIStage.GET_CMD


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

    t(shell_sym="$")


if __name__ == "__main__":
    main()
