"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Self

import colorlog
from cognition import (
    Actuator,
    AutoDocEnum,
    Cogent,
    DecisionProcess,
    IOContainer,
    Sensor,
    StagedState,
    staged_operator,
    stringify,
)
from rich import print as rprint
from rich.prompt import Prompt

###################################################
# Logging setup
###################################################

handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(fmt="%(log_color)s%(levelname)s\t%(name)s\t%(message)s")
)

logger = colorlog.getLogger("cognition")
logger.setLevel(colorlog.WARNING)
logger.addHandler(handler)

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


# ===

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

    return CommandReturn("\n".join(str(entry) for entry in cli_dp.state.log), 0, False)


###################################################
# CLI sensing/actuating
###################################################


class CurrentCommand(Sensor[str], Actuator[str, None]):
    """
    Getting/setting the current CLI command
    """

    def __init__(self) -> None:
        self._cmd = ""

    @property
    def name(self) -> str:
        return "cli"

    def sense(self) -> str:
        return self._cmd

    def actuate(self, param: str) -> None:
        self._cmd = Prompt.ask(f"[bold blue]{ param }[/]")


cli_sensor_actuator = CurrentCommand()

###################################################
# CLI decision process and state definitions
###################################################


class CLIStage(AutoDocEnum):
    """Step of CLI processing"""

    INIT = "welcome the user"
    GET_CMD = "get the command"
    EXEC_CMD = "execute the command"
    EXIT = "exit flag detected on cmd result"


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
class CLIState(StagedState[CLIStage]):
    """
    State of the CLI program
    """

    stage: CLIStage = CLIStage.INIT
    """INIT -> (GET <-> EXEC) -?-> EXIT"""

    log: list[CommandLogEntry] = field(default_factory=list)
    """Log of command executions"""

    # ===

    def init(self) -> CLIStage:
        """transition to... getting the (first) command"""

        return CLIStage.GET_CMD

    def get_cmd(self) -> CLIStage:
        """transition to... command execution"""

        return CLIStage.EXEC_CMD

    def exec_cmd(self, log_entry: CommandLogEntry) -> CLIStage:
        """
        process the log entry;
        then transition to... getting the (next) command
        """

        self.log.append(log_entry)
        log_entry.result.print()

        if log_entry.result.exit:
            return CLIStage.EXIT

        return CLIStage.GET_CMD


cli_state = CLIState()
persistent_state = stringify("keep")(lambda: cli_state)

# ===

cli_dp = DecisionProcess(persistent_state)


@staged_operator(cli_dp, CLIStage.INIT)
def perform_init(_s: CLIState, _io: IOContainer) -> None:
    """init action"""

    rprint("Welcome to SimpleCLI")
    rprint("Enter [code]help[/] to see available commands.")
    rprint()


@staged_operator(cli_dp, CLIStage.GET_CMD, terminal=True)
def perform_get(_s: CLIState, io: IOContainer) -> None:
    """get action"""

    shell_sym = io.i.args.shell_sym

    # options...
    # cli_sensor_actuator.invoker(io, shell_sym)
    io.o.cli(shell_sym)


@staged_operator(cli_dp, CLIStage.EXEC_CMD, terminal=True)
def perform_exec(_s: CLIState, io: IOContainer) -> Mapping[str, Any]:
    """exec action"""

    # options...
    # cmd = cli_sensor_actuator.reader(io)
    cmd = io.i.cli

    return {"log_entry": CommandLogEntry.attempt_exec(cmd)}


###################################################
# Cogent loop
###################################################


@stringify("go_until_exit")
def go_until_exit(dp: DecisionProcess[CLIState]) -> bool:
    """continue until exit stage"""

    return dp.state.stage is not CLIStage.EXIT


###################################################
# Start the app
###################################################


def main() -> None:
    """dispatch the cli agent"""

    Cogent(cli_dp, "cli").add_sensor(cli_sensor_actuator).add_actuator(
        cli_sensor_actuator
    )(go_until_exit, shell_sym="$")


if __name__ == "__main__":
    main()
