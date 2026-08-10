"""
Definitions for DP state
"""

from dataclasses import dataclass, field

from cognition import AutoDocEnum, SelfReinitState, StagedState

from commands import CommandLogEntry

# ===


class CLIStage(AutoDocEnum):
    """Step of CLI processing"""

    INIT = "welcome the user"
    GET_CMD = "get the command"
    EXEC_CMD = "execute the command"
    EXIT = "exit flag detected on cmd result"


@dataclass
class CLIState(StagedState[CLIStage], SelfReinitState):
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
