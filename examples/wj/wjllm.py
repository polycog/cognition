"""
LLM code for WaterJug
"""

from typing import Optional

import streamlit as st

from openai import OpenAI

from pydantic import BaseModel, Field, ValidationError

##################################################

LLM_SECRET: str = "llm"
LLM_MODEL: str = "openai/gpt-oss-20b"

#

class ProblemConfig(BaseModel):
    """
    WaterJug problem configuration
    """

    vol1: int = Field(description="Volume of the first jug")
    vol2: int = Field(description="Volume of the second jug")
    desired: int = Field(description="Desired volume to achieve (in either of the jugs)")


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

@st.cache_resource
def _get_client(secret_section: str) -> OpenAI:
    client = OpenAI(**st.secrets[secret_section])

    # make sure connection actually works
    client.models.list()

    return client

def llm_try_connect() -> None:
    """
    Attempts LLM connection
    """

    try:
        _ = _get_client(LLM_SECRET)
    except Exception as e: # pylint: disable=broad-exception-caught
        st.exception(e)

#

@st.cache_data
def llm_user_prompt(desc: str) -> str:
    """
    Provides the user prompt (with added instruction)
    """

    return f"{desc}. {LLM_JSON_REMINDER}"

@st.cache_data
def llm_convert_description(desc: str) -> Optional[ProblemConfig]:
    """
    Converts from a supplied prompt to
    an associated problem configuration
    """

    try:
        response = _get_client(LLM_SECRET).responses.parse(
            model=LLM_MODEL,
            instructions=LLM_SYSTEM_PROMPT,
            input=llm_user_prompt(desc),
            text_format=ProblemConfig,
        )

        return response.output_parsed
    except ValidationError as e:
        st.exception(e)
        return None
