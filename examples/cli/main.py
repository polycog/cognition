"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from __future__ import annotations

from typing import Any, Self

from collections.abc import Callable

from dataclasses import dataclass, field

from contextlib import nullcontext

from cognition import (
    AttrReferral,
    AutoDocEnum,
    EnhancedTask,
    EnumDispatch,
    IOContainer,
    NamedOperator,
    stringify,
)

from rich import print as rprint
from rich.prompt import Prompt

###################################################
# Command definition and support
###################################################


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


type Command = Callable[[], CommandReturn]
"""our commands take no arguments and produce text + code + exit flag"""


def register_command(dest: dict[str, Command]) -> Callable[[Command], Command]:
    """adds a command to the destination"""

    def dec(cmd: Command) -> Command:
        """actually registers the command"""

        dest[str(cmd)] = cmd
        return cmd

    return dec


#

registered_commands: dict[str, Command] = {}
"""registered as {str(cmd): callable}"""


@register_command(registered_commands)
@stringify("help")
def cmd_help() -> CommandReturn:
    """List of available commands"""

    return CommandReturn(
        f"Available commands: {", ".join(registered_commands.keys())}", 0, False
    )


@register_command(registered_commands)
@stringify("hello")
def cmd_hello() -> CommandReturn:
    """Friendly!!"""

    return CommandReturn(":smile:", 0, False)


@register_command(registered_commands)
@stringify("err")
def cmd_err() -> CommandReturn:
    """Badness"""

    return CommandReturn(
        ":scream: What we've got here is... failure to communicate", 1, False
    )


@register_command(registered_commands)
@stringify("bye")
def cmd_bye() -> CommandReturn:
    """Exit"""

    return CommandReturn(":waving_hand:", 0, True)


@register_command(registered_commands)
@stringify("history")
def cmd_history() -> CommandReturn:
    """Log of past interactions"""

    return CommandReturn("\n".join(str(entry) for entry in t.state.log), 0, False)


###################################################
# CLI task and state definitions
###################################################


class CLIStage(AutoDocEnum):
    """Step of CLI processing"""

    INIT = "welcome the user"
    GET_CMD = "get the command"
    EXEC_CMD = "execute the command"


@dataclass(frozen=True)
class CommandLogEntry:
    """A past command with its result"""

    cmd: str
    result: CommandReturn

    @classmethod
    def attempt_exec(cls, user_input: str) -> Self:
        """produce a log entry via a user input"""

        return cls(
            user_input,
            (
                CommandReturn.invalid(user_input)
                if user_input not in registered_commands
                else registered_commands[user_input]()
            ),
        )


@dataclass
class CLIState(EnumDispatch[CLIStage]):
    """
    Current stage (get/exec)
    +
    Log of past commands
    """

    stage: CLIStage = CLIStage.INIT
    log: list[CommandLogEntry] = field(default_factory=list)

    def transition(self, *args: Any, **kwargs: Any) -> None:
        """update state (per stage)"""

        self.stage = self(self.stage, *args, **kwargs)

    def init(self) -> CLIStage:
        """proceed to getting the first command"""

        return CLIStage.GET_CMD

    def get_cmd(self) -> CLIStage:
        """proceed to execution"""

        return CLIStage.EXEC_CMD

    def exec_cmd(self, log_entry: CommandLogEntry) -> CLIStage:
        """process the log entry and proceed to getting the next command"""

        self.log.append(log_entry)
        log_entry.result.print()

        return CLIStage.GET_CMD


#

with nullcontext[dict[str, str]]({}) as cli_status:
    # cli_status is a shared reference to a dictionary
    # used to represent the user-entered command

    t = (
        EnhancedTask(CLIState)
        .set_sensor(
            "cli", AttrReferral(cli_status)
        )  # expose the current command via io.i.cli
        .set_actuator(
            "cli_set_command", lambda c: cli_status.update(command=c)
        )  # change current command via io.o
    )


@t.operator(CLIStage.INIT.name)
class Init(NamedOperator[CLIState]):
    """welcome the user"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.INIT

    def perform(self, state: CLIState, io: IOContainer) -> None:
        rprint("Welcome to SimpleCLI")
        rprint("Enter [code]help[/] to see available commands.")
        rprint()

        state.transition()


@t.operator(CLIStage.GET_CMD.name)
class GetCommand(NamedOperator[CLIState]):
    """show the prompt + get user input"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.GET_CMD

    def perform(self, state: CLIState, io: IOContainer) -> None:
        io.o.cli_set_command(Prompt.ask(f"[bold blue]{ io.i.args.shell_sym }[/]"))
        state.transition()


@t.operator(CLIStage.EXEC_CMD.name)
class ExecCommand(NamedOperator[CLIState]):
    """try to execute the command + log the result"""

    def can_perform(self, state: CLIState, _io: IOContainer) -> bool:
        return state.stage == CLIStage.EXEC_CMD

    def perform(self, state: CLIState, io: IOContainer) -> None:
        state.transition(CommandLogEntry.attempt_exec(io.i.cli.command))


@t.goal_check
@stringify("exit_flag")
def exit_flag(s: CLIState, _: IOContainer) -> bool:
    """Exit if told to!"""

    if s.log:
        return s.log[-1].result.exit

    return False


###################################################
# Start the app
###################################################


def main() -> None:
    """dispatch the cli agent"""

    # argument: prompt symbol (accessed via io.i.args)
    t(shell_sym="$")


if __name__ == "__main__":
    main()
