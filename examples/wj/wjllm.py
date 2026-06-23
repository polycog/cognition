"""
LLM code for WaterJug
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model

from dotenv import load_dotenv

load_dotenv()

##################################################

AGENT_FILE: str = "agent.yaml"

#


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


#


LLM_EXAMPLE_INPUT: str = (
    "There are two jugs: "
    "a five gallon and a three gallon; "
    "fill one of the jugs with exactly 4 gallons of water."
)
LLM_EXAMPLE_OUTPUT: str = '{ "vol1": 3, "vol2": 5, "desired": 4 }'

LLM_JSON_REMINDER: str = "Return ONLY valid JSON that matches the provided schema."

LLM_SYSTEM_PROMPT: str = f"""
You are a helpful assistant.
Please help me to describe an instance of a classic WaterJug puzzle.
In WaterJug, you use two jugs with fixed, different capacities (like 3 and 5) to measure a precise amount of water (e.g., 4), with no markings on the jugs, by filling, emptying, and pouring between them to reach a target volume.
At this point we just need to understand the user's intended configuration of the problem: the volumes of the two jugs, as well as the desired goal volume, neither of which need to take into account units of measurement.
{LLM_JSON_REMINDER}
For example, if told that '{LLM_EXAMPLE_INPUT}' then we know the jug volumes are 3 and 5,
with a desired goal of 4, and so return {LLM_EXAMPLE_OUTPUT}.
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

    return f"{desc}. {LLM_JSON_REMINDER}"


def llm_parse_config(agent: Agent[str, WJConfig], desc: str) -> WJConfig:
    """
    Attempts to convert a string to a configuration
    """

    try:
        return agent.run_sync(llm_user_prompt(desc)).output
    except Exception as e:
        raise LLMException(e) from e
