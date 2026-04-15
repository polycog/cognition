"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from __future__ import annotations

from collections.abc import (
    Callable,
    Iterable,
)

from dataclasses import dataclass

from enum import IntEnum

from cognition import (
    Action,
    AttrReferral,
    IOContainer,
    Task,
    stringify,
)

from rich import print as rprint
from rich.prompt import Prompt

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

t: Task[CLIState] = Task(lambda: CLIState(CLIStage.GET_CMD, []))

# shared reference to
# command input buffer
cli_status: dict[str, str] = {}
t.set_sensor("cli", AttrReferral(cli_status))

#

@t.action_factory
def prompt_factory(s: CLIState, _: IOContainer) -> Iterable[Action[CLIState]]:
    """Get next command"""

    if s.stage != CLIStage.GET_CMD:
        return []

    #

    @stringify("get_command")
    def _exec(s: CLIState, __: IOContainer) -> None:
        s.stage = s.stage.next()
        cli_status["command"] = Prompt.ask("[bold blue]$[/]")

    return [_exec]

@t.action_factory
def cmd_factory(s: CLIState, io: IOContainer) -> Iterable[Action[CLIState]]:
    """Either invalid or a registered command"""

    if s.stage != CLIStage.EXEC_CMD:
        return []

    #

    cmd = io.i.cli.command

    if cmd in commands:
        log_entry = CommandLogEntry(cmd, commands[cmd]())
    else:
        log_entry = CommandLogEntry(
            cmd,
            CommandReturn(f"Invalid command: {cmd}", 1, False)
        )

    @stringify("exec_command")
    def _exec(s: CLIState, _: IOContainer) -> None:
        s.stage = s.stage.next()

        s.log.append(log_entry)

        if log_entry.result.code != 0:
            rprint(f"[bold red]{log_entry.result.text}[/]")
        else:
            rprint(log_entry.result.text)
        print()

    return [_exec]

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
