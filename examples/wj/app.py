"""
WaterJug streamlit main code
"""

from typing import Optional

import streamlit as st
import pandas as pd

from wjllm import (
    LLM_EXAMPLE_INPUT,
    LLM_MODEL,
    LLM_SYSTEM_PROMPT,
    ProblemConfig,
    llm_convert_description,
    llm_try_connect,
    llm_user_prompt,
)

from wjplan import (
    InvalidConfiguration,
    Success,
    TooLong,
    WJResult,
    run_waterjug
)

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
    page_title=F"{APP_NAME}: {APP_DESC}",
    page_icon=APP_ICON,
    layout="wide"
)

##################################################

with st.container(border=False):
    f"""
    # {APP_ICON} {APP_NAME}

    {APP_DESC}
    """

    llm_try_connect()


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
        placeholder=LLM_EXAMPLE_INPUT
    )

    with st.expander("See movie reference"):
        st.video("https://youtu.be/m9F0i-1Jys0")

    if desc:
        conversion: Optional[ProblemConfig] = llm_convert_description(desc)

        if conversion:
            st.session_state[KEY_LLM_OUTPUT] = conversion

            with st.expander("See details of LLM conversion"):
                st.write(f"Using model: `{LLM_MODEL}`")

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

if all(k in st.session_state for k in (KEY_MAXSTEPS, KEY_LLM_OUTPUT)):
    prob: ProblemConfig = st.session_state[KEY_LLM_OUTPUT]

    result: WJResult = run_waterjug(
        vol1 = prob.vol1,
        vol2 = prob.vol2,
        desired = prob.desired,
        max_steps = st.session_state[KEY_MAXSTEPS]
    )

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
                        columns=['Action', 'First Jug (contents)', 'Second Jug (contents)']
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

                chart_data = pd.DataFrame({
                    'First Jug': [first_jug, prob.vol1 - first_jug],
                    'Second Jug': [second_jug, prob.vol2 - second_jug]
                }, index=['Filled', 'Empty'])

                st.bar_chart(chart_data.T)
