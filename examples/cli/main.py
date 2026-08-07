"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from collections.abc import Mapping
from typing import Any

from cognition import (
    Actuator,
    Cogent,
    DecisionProcess,
    IOContainer,
    Sensor,
    staged_operator,
    stringify,
)
from rich import print as rprint
from rich.prompt import Prompt

from commands import CommandLogEntry
from dp_state import CLIStage, CLIState
from log_support import setup_logging

# ===

setup_logging()

###################################################
# Agent construction
###################################################

# dp state
cli_state = CLIState()
persistent_state = stringify("keep")(lambda: cli_state)

# cogent (pending operators, sensing/actuation)
cli_cogent = Cogent(DecisionProcess(persistent_state), "cli")


###################################################
# Command sensing/actuating
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
cli_cogent.add_sensor(cli_sensor_actuator).add_actuator(cli_sensor_actuator)

###################################################
# CLI decision process and state definitions
###################################################


@staged_operator(cli_cogent.dp, CLIStage.INIT)
def perform_init(_s: CLIState, _io: IOContainer) -> None:
    """init action"""

    rprint("Welcome to SimpleCLI")
    rprint("Enter [code]help[/] to see available commands.")
    rprint()


@staged_operator(cli_cogent.dp, CLIStage.GET_CMD, terminal=True)
def perform_get(_s: CLIState, io: IOContainer) -> None:
    """get action"""

    shell_sym = io.i.args.shell_sym

    # options...
    # cli_sensor_actuator.invoker(io, shell_sym)
    io.o.cli(shell_sym)


@staged_operator(cli_cogent.dp, CLIStage.EXEC_CMD, terminal=True)
def perform_exec(s: CLIState, io: IOContainer) -> Mapping[str, Any]:
    """exec action"""

    # options...
    # cmd = cli_sensor_actuator.reader(io)
    cmd = io.i.cli

    return {"log_entry": CommandLogEntry.attempt_exec(cmd, s.log)}


###################################################
# Cogent loop gating
###################################################


@stringify("go_until_exit")
def go_until_exit(c: Cogent[DecisionProcess[CLIState]]) -> bool:
    """continue until exit stage"""

    return c.dp.state.stage is not CLIStage.EXIT


###################################################
# Start the app
###################################################


def main() -> None:
    """dispatch the cli agent"""

    cli_cogent(go_until_exit, shell_sym="$")


if __name__ == "__main__":
    main()
