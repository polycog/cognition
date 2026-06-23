"""
WaterJug streamlit main code
"""

from typing import Optional

import streamlit as st
import pandas as pd

from wjllm import (
    LLM_EXAMPLE_INPUT,
    LLM_SYSTEM_PROMPT,
    ConfigFail,
    LLMException,
    ProblemConfig,
    llm_init,
    llm_model_name,
    llm_parse_config,
    llm_user_prompt,
)

from wjplan import InvalidConfiguration, Success, TooLong, WJResult, run_waterjug

# pylint: disable=pointless-statement
# pylint: disable=pointless-string-statement

##################################################

APP_ICON: str = ":material/balance:"
APP_NAME: str = "WaterJug"
APP_DESC: str = "Neuro-Symbolic Puzzle Solving"

KEY_DESC: str = "description"
KEY_MAXSTEPS: str = "maxsteps"
KEY_LLM_OUTPUT: str = "config"

#

st.set_page_config(
    page_title=f"{APP_NAME}: {APP_DESC}", page_icon=APP_ICON, layout="wide"
)

##################################################

with st.container(border=False):
    f"""
    # {APP_ICON} {APP_NAME}

    {APP_DESC}
    """

    try:
        llm = llm_init()
    except LLMException as e:
        st.exception(e)


@st.cache_data
def run_llm(description: str) -> Optional[ProblemConfig]:
    """Invokes llm to try to parse problem configuration from text"""

    if llm:
        parse_result = llm_parse_config(llm, description)

        if isinstance(parse_result, ProblemConfig):
            return parse_result

        if isinstance(parse_result, ConfigFail):
            st.warning(parse_result.msg)

    return None


with st.container(border=True):
    """
    ## Problem Description
    """

    desc = st.text_area(
        (
            "Be sure to indicate the volumes of the two jugs "
            "and the desired volume (to be found in either jug)."
        ),
        key=KEY_DESC,
        placeholder=LLM_EXAMPLE_INPUT,
    )

    with st.expander("See movie reference"):
        st.video("https://youtu.be/m9F0i-1Jys0")

    if desc:
        conversion: Optional[ProblemConfig] = run_llm(desc)

        if conversion:
            st.session_state[KEY_LLM_OUTPUT] = conversion

            with st.expander("See details of LLM conversion"):
                st.write(f"Using model: `{llm_model_name(llm)}`")

                with st.chat_message("system"):
                    st.write(LLM_SYSTEM_PROMPT)

                with st.chat_message("user"):
                    st.write(llm_user_prompt(desc))

                with st.chat_message("ai"):
                    st.code(conversion)
    else:
        if KEY_LLM_OUTPUT in st.session_state:
            del st.session_state[KEY_LLM_OUTPUT]


with st.container(border=True):
    """
    ## Advanced Options
    """

    st.number_input(
        "Maximum planner steps to attempt solution",
        key=KEY_MAXSTEPS,
        min_value=1,
        step=1,
        value=100,
    )


@st.cache_data
def run_planner(prob_config: ProblemConfig, max_steps: int) -> WJResult:
    """Invokes planner to try to solve the problem given the steps"""

    return run_waterjug(
        vol1=prob_config.vol1,
        vol2=prob_config.vol2,
        desired=prob_config.desired,
        max_steps=max_steps,
    )


if all(k in st.session_state for k in (KEY_MAXSTEPS, KEY_LLM_OUTPUT)):
    prob: ProblemConfig = st.session_state[KEY_LLM_OUTPUT]
    result: WJResult = run_planner(prob, st.session_state[KEY_MAXSTEPS])

    #

    with st.container(border=True):
        f"""
        ## Results

        * First jug's capacity: {prob.vol1}
        * Second jug's capacity: {prob.vol2}
        * Target water volume: {prob.desired}
        """

        match result:
            case InvalidConfiguration(msg=m):
                st.error(m)

            case TooLong(cycles=c):
                st.warning(
                    f"Did not complete given max steps ({c}); "
                    "you can try extending this limit or choose a different seed."
                )

            case Success(cycles=c, plan=p):
                st.success(f"Success (in {c} planner steps)")

                st.dataframe(
                    pd.DataFrame(
                        p,
                        columns=[
                            "Action",
                            "First Jug (contents)",
                            "Second Jug (contents)",
                        ],
                    )
                )

                #

                row_index = st.slider("Select action to view", 0, len(p) - 1, 0)
                selected_row = p[row_index]

                #

                f"""
                ### {selected_row[0]}
                """

                first_jug = selected_row[1]
                second_jug = selected_row[2]

                chart_data = pd.DataFrame(
                    {
                        "First Jug": [first_jug, prob.vol1 - first_jug],
                        "Second Jug": [second_jug, prob.vol2 - second_jug],
                    },
                    index=["Filled", "Empty"],
                )

                st.bar_chart(chart_data.T)
