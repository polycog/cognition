"""
LLM code for WaterJug
"""

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model

load_dotenv()

##################################################

AGENT_FILE: str = "agent.yaml"

# ===


class LLMException(Exception):
    """Raised for various LLM-related issues"""


class ProblemConfig(BaseModel):
    """
    WaterJug problem configuration
    """

    vol1: int = Field(description="Volume of the first jug")
    vol2: int = Field(description="Volume of the second jug")
    desired: int = Field(
        description="Desired volume to achieve (in either of the jugs)"
    )


class ConfigFail(BaseModel):
    """
    No reasonable WaterJug problem detected
    """

    msg: str = Field(description="Feedback from a parse failure")


type WJConfig = ProblemConfig | ConfigFail


# ===


LLM_EXAMPLE_INPUT: str = (
    "There are two jugs: "
    "a five gallon and a three gallon; "
    "fill one of the jugs with exactly 4 gallons of water."
)
LLM_EXAMPLE_OUTPUT: str = ProblemConfig(vol1=5, vol2=3, desired=4).model_dump_json()

LLM_EXAMPLE_BAD_INPUT: str = "Where can I buy water?"
LLM_EXAMPLE_BAD_OUTPUT: str = ConfigFail(
    msg="Unable to parse WaterJug configuration from input."
).model_dump_json()

LLM_SYSTEM_PROMPT: str = "You are a helpful assistant."

LLM_USER_PROMPT: str = """
Please help me to describe an instance of a WaterJug problem.

[General Context]

In WaterJug, you use two jugs with fixed, different capacities (like 3 and 5) to measure a precise amount of water (e.g., 4), with no markings on the jugs, by filling, emptying, and pouring between them to reach a target volume.
I just need to understand the user's intended configuration of the problem: the volumes of the two jugs, as well as the desired goal volume, neither of which need to take into account units of measurement.

[Output Requirements]

1. Return ONLY valid JSON that matches the provided schema.
2. If the supplied text cannot be parsed as a reasonable WaterJug problem, there is a configuration failure option.

[Examples]

1. Given '{}'...
   a configuration would be: {}

2. However, given an input that is clearly not a WaterJug description (e.g., '{}')...
   a response might be: {}

[Problem Description]

'{}'

Please extract the problem configuration (or failure if not reasonable).
"""

##################################################


def llm_init() -> Agent[str, WJConfig]:
    """
    Produces the LLM agent
    """

    try:
        return Agent.from_file(  # type: ignore
            AGENT_FILE, output_type=WJConfig, system_prompt=LLM_SYSTEM_PROMPT
        )
    except Exception as e:
        raise LLMException(f"Error creating agent from {AGENT_FILE}: {e}") from e


def llm_model_name(agent: Agent[str, WJConfig]) -> str:
    """Best attempt at model identification"""

    if isinstance(agent.model, Model):
        return agent.model.model_name

    return str(agent.model)


def llm_user_prompt(desc: str) -> str:
    """
    Provides the user prompt (with added instruction)
    """

    return LLM_USER_PROMPT.format(
        LLM_EXAMPLE_INPUT,
        LLM_EXAMPLE_OUTPUT,
        LLM_EXAMPLE_BAD_INPUT,
        LLM_EXAMPLE_BAD_OUTPUT,
        desc,
    )


def llm_parse_config(agent: Agent[str, WJConfig], desc: str) -> WJConfig:
    """
    Attempts to convert a string to a configuration
    """

    try:
        return agent.run_sync(llm_user_prompt(desc)).output
    except Exception as e:
        raise LLMException(e) from e
