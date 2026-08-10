"""
Skeleton of a CLI as a
demonstration of the
cognition library
"""

from collections.abc import Mapping
from typing import Any, overload

from cognition import (
    Cogent,
    DecisionProcess,
    IOContainer,
    self_actuator,
    self_sensor,
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


class CLICogent(Cogent[DecisionProcess[CLIState]]):
    """
    Cogent, with integrated sensing/actuation
    """

    def __init__(self, name: str = "cli", **kwargs: Any) -> None:
        super().__init__(DecisionProcess(CLIState()), name=name, **kwargs)

        self._cmd = ""

    @overload
    def cmd(self) -> str:
        """cmd sensor"""

    @overload
    def cmd(self, param: str) -> None:
        """cmd actuator"""

    @self_actuator  # type: ignore
    @self_sensor
    def cmd(self, param: str | None = None) -> str | None:
        """get/set current cmd"""

        if param is None:
            return self._cmd

        self._cmd = Prompt.ask(f"[bold blue]{ param }[/]")
        return None


cli_cogent = CLICogent()

###################################################
# Decision process via state stage
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

    io.o.cmd(io.i.args.shell_sym)


@staged_operator(cli_cogent.dp, CLIStage.EXEC_CMD, terminal=True)
def perform_exec(s: CLIState, io: IOContainer) -> Mapping[str, Any]:
    """exec action"""

    return {"log_entry": CommandLogEntry.attempt_exec(io.i.cmd, s.log)}


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
