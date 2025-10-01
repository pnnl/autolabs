from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
import pandas as pd
import streamlit as st
import numpy as np
import re
from .tag_utils import get_chem_state
from .config import Client
import ast

completer = Client("unfiltered")


tags_values = [
    "ZSample",
    "MoveVial",
    "250uLTip",
    "BalancePictureOnly",
    "SourceTracking",
    "Backsolvent",
    "Manual",
    "LookAhead",
    "Chaser",
    "Powder",
    "Uncap",
    "SyringePump",
    "Filter StepCap",
    "Plate",
    "NewTip",
    "Filter",
    "SkipMap",
    "Filter CompletePress",
    "ScrewCap",
    "ExtSingleTip",
    "Image",
    "PDT",
    "1000uLTip",
    "4Tip",
    "50uLTip",
    "100uLTip",
    "10mLTip",
    "StartReactionTimer",
    "Hover",
    "Analysis",
    "Wait",
    "CapAfterDispense",
    "Processing",
    "HPTare",
    "DestinationTracking",
    "Filter StepPartialPress",
    "HighResPictureOnly",
]

# data_source = pd.read_pickle('data/tags.pkl')
# data_params = pd.read_pickle('data/tags_params.pkl')


example_prompt = PromptTemplate(
    input_variables=["step", "tags"], template="step:{step}\noptions:{tags}"
)


def clean_tag(tag):

    tag = tag.replace(" ", "")
    tag = re.sub(r"\W+", "", tag)

    return tag


def save_options():
    st.session_state.tag_options.append(
        {st.session_state.step_text: st.session_state.step_options}
    )


def level1():
    st.session_state.level1_option = st.session_state.level1


def SyringePump():
    optional_tags = list(
        np.array(
            [
                "Backsolvent",
                "LookAhead",
                "SourceTracking",
                "DestinationTracking",
                "Hover",
                "StartVialTimer",
                "WaitVialTimer",
                "Notify",
            ]
        )[
            [
                st.session_state.op1,
                st.session_state.op2,
                st.session_state.op3,
                st.session_state.op4,
                st.session_state.op5,
                st.session_state.op6,
                st.session_state.op7,
                st.session_state.op8,
            ]
        ]
    )

    st.session_state.tag_options.append(
        {
            st.session_state.step_text: [st.session_state.level1_option]
            + st.session_state.level2
            + optional_tags
        }
    )
    st.session_state.tag_counter += 1
    st.session_state.level1_option = None


def PDT():
    optional_tags = list(
        np.array(
            [
                "LookAhead",
                "CapAfterDispense",
                "NewTip",
                "StartVialTimer",
                "WaitVialTimer",
                "Notify",
            ]
        )[
            [
                st.session_state.op1,
                st.session_state.op2,
                st.session_state.op3,
                st.session_state.op4,
                st.session_state.op5,
                st.session_state.op6,
                st.session_state.op7,
                st.session_state.op8,
                st.session_state.op9,
                st.session_state.op10,
            ]
        ]
    )
    st.session_state.tag_options.append(
        {
            st.session_state.step_text: [
                st.session_state.level1_option,
                st.session_state.level2,
            ]
            + optional_tags
        }
    )
    st.session_state.tag_counter += 1
    st.session_state.level1_option = None


def FourTip():
    optional_tags = list(
        np.array(
            ["Backsolvent", "LookAhead", "StartVialTimer", "WaitVialTimer", "Notify"]
        )[
            [
                st.session_state.op1,
                st.session_state.op2,
                st.session_state.op3,
                st.session_state.op4,
                st.session_state.op5,
                st.session_state.op6,
                st.session_state.op7,
            ]
        ]
    )
    st.session_state.tag_options.append(
        {st.session_state.step_text: [st.session_state.level1_option] + optional_tags}
    )
    st.session_state.tag_counter += 1
    st.session_state.level1_option = None


def Powder():
    optional_tags = list(
        np.array(["Plate", "Notify"])[[st.session_state.op1, st.session_state.op2]]
    )
    st.session_state.tag_options.append(
        {st.session_state.step_text: [st.session_state.level1] + optional_tags}
    )
    st.session_state.tag_counter += 1
    st.session_state.level1_option = None


def MoveVial():
    optional_tags = list(
        np.array(["StartVialTimer", "WaitVialTimer", "Notify"])[
            [st.session_state.op1, st.session_state.op2]
        ]
    )
    st.session_state.tag_options.append(
        {st.session_state.step_text: [st.session_state.level1] + optional_tags}
    )
    st.session_state.tag_counter += 1
    st.session_state.level1_option = None


import pickle
import os
from .prompts import additions_prompt_level1, additions_prompt_level2, tags_prompt


def select_tags():

    if st.session_state.tag_counter < len(st.session_state.steps):

        i = st.session_state.tag_counter
        st.session_state.step_text = st.session_state.steps[
            i
        ].get_text()  # selected step

        current_step_text = st.session_state.step_text
        current_step_text_loc = current_step_text.find("{")
        current_step_text = current_step_text[:current_step_text_loc]

        with st.chat_message("system"):
            message = f"Please make corrections to the suggested tags for the {current_step_text} step?"
            st.markdown(message)

        if st.session_state.tag_counter == 0:
            message_init = f"{tags_prompt}"
            st.session_state.chat_history.append(
                {"role": "system", "content": message_init}
            )

        if (
            "add" in current_step_text.lower()
            and st.session_state.level1_option is None
        ):

            chem_name, _chem_state = get_chem_state(completer, current_step_text)

            if "(mg)" in current_step_text.lower():
                chem_state = "solid"
            elif "(ul)" in current_step_text.lower():
                chem_state = "liquid"
            else:
                chem_state = _chem_state

            print("chem_state: ", chem_state)

            if chem_state == "solid":
                default = "Powder"
            else:
                option_prompt = f"""
                    You have to decide the chemical instrument option based on the on the following criteria.
                    - chemical is water or water miscible liquid and array dim is 8x12 -> "4Tip"
                    - chemical is water or water miscible liquids and array dim is NOT 8X12 -> "SyringePump"
                    - chemical is water immiscible -> "PDT" 
                    chemical: {chem_name}.
                    array dim: {st.session_state.array_dim}.
                    return only the option (one of "4Tip", "SyringePump" or "PDT").
                    """

                messages = [
                    *st.session_state.chat_history,
                    {"role": "system", "content": option_prompt},
                ]
                response = completer.get_chat_completions(messages)
                assistant_response = response.choices[0].message.content
                selected_tags = []
                for tag in ["SyringePump", "PDT", "4Tip"]:
                    if tag in assistant_response:
                        selected_tags.append(tag)

                if len(selected_tags) == 0:
                    default = "SyringePump"
                else:
                    default = selected_tags[0]

            all_level1_options = ["Powder", "SyringePump", "PDT", "4Tip"]
            with st.form(key="level1_form"):
                options = st.selectbox(
                    "Dispensing Tags",
                    [default] + [i for i in all_level1_options if i != default],
                    key="level1",
                )
                l1 = st.form_submit_button(
                    label="Select Main Dispensing Tag", on_click=level1
                )

        elif (
            "add" in current_step_text.lower()
            and st.session_state.level1_option is not None
        ):
            if st.session_state.level1_option == "SyringePump":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["SyringePump"], key="level1", disabled=True
                    )

                    second_level_tags = st.selectbox("", ["ExtSingleTip"], key="level2")

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                            experiment step: {current_step_text}\n
                            high-level dispensing tag: SyringePump\n
                            context: {additions_prompt_level2}\n
                            return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                            the tags should be selected from the options ['Backsolvent', 'LookAhead', 'SourceTracking', 'DestinationTracking',
                            'Hover', 'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                            """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)

                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]
                    }

                    op1 = st.checkbox(
                        "Backsolvent", key="op1", value=op_dict["Backsolvent"]
                    )
                    op2 = st.checkbox(
                        "LookAhead", key="op2", value=op_dict["LookAhead"]
                    )
                    op3 = st.checkbox(
                        "SourceTracking", key="op3", value=op_dict["SourceTracking"]
                    )
                    op4 = st.checkbox(
                        "DestinationTracking",
                        key="op4",
                        value=op_dict["DestinationTracking"],
                    )
                    op5 = st.checkbox("Hover", key="op5", value=op_dict["Hover"])
                    op6 = st.checkbox(
                        "StartVialTimer", key="op6", value=op_dict["StartVialTimer"]
                    )
                    op7 = st.checkbox(
                        "WaitVialTimer", key="op7", value=op_dict["WaitVialTimer"]
                    )
                    op8 = st.checkbox("Notify", key="op8", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=SyringePump
                    )

            elif st.session_state.level1_option == "PDT":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["PDT"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                            experiment step: {current_step_text}\n
                            high-level dispensing tag: PDT\n
                            context: {additions_prompt_level2}\n
                            return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                            the tags should be selected from the options ['LookAhead', 'SourceTracking', 'DestinationTracking',
                            'Hover', 'StartVialTimer', 'WaitVialTimer','Notify','ZSample','CapAfterDispense','NewTip'] and the available PDT size tags.
                            """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)
                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                            "ZSample",
                            "CapAfterDispense",
                            "NewTip",
                        ] + [
                            "10mLTip",
                            "1000uLTip",
                            "250uLTip" "100uLTip",
                            "50uLTip",
                            "25uLTip",
                            "10uLTip",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    size_tag = [
                        t
                        for t in options
                        if t
                        in [
                            "10mLTip",
                            "1000uLTip",
                            "250uLTip" "100uLTip",
                            "50uLTip",
                            "25uLTip",
                            "10uLTip",
                        ]
                    ]
                    if len(size_tag) == 0:
                        size_tag = "10mLTip"
                    else:
                        size_tag = size_tag[0]

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                            "ZSample",
                            "CapAfterDispense",
                            "NewTip",
                        ]
                    }

                    second_level_tags = st.selectbox(
                        "",
                        [size_tag]
                        + [
                            t
                            for t in [
                                "10mLTip",
                                "1000uLTip",
                                "250uLTip" "100uLTip",
                                "50uLTip",
                                "25uLTip",
                                "10uLTip",
                            ]
                            if t != size_tag
                        ],
                        key="level2",
                    )

                    op1 = st.checkbox(
                        "LookAhead", key="op1", value=op_dict["LookAhead"]
                    )
                    op2 = st.checkbox(
                        "SourceTracking", key="op2", value=op_dict["SourceTracking"]
                    )
                    op3 = st.checkbox(
                        "DestinationTracking",
                        key="op3",
                        value=op_dict["DestinationTracking"],
                    )
                    op4 = st.checkbox("ZSample", key="op4", value=op_dict["ZSample"])
                    op5 = st.checkbox("Hover", key="op5", value=op_dict["Hover"])
                    op6 = st.checkbox(
                        "CapAfterDispense", key="op6", value=op_dict["CapAfterDispense"]
                    )
                    op7 = st.checkbox("NewTip", key="op7", value=op_dict["NewTip"])
                    op8 = st.checkbox(
                        "StartVialTimer", key="op8", value=op_dict["StartVialTimer"]
                    )
                    op9 = st.checkbox(
                        "WaitVialTimer", key="op9", value=op_dict["WaitVialTimer"]
                    )
                    op10 = st.checkbox("Notify", key="op10", value=op_dict["Notify"])

                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=PDT
                    )

            elif st.session_state.level1_option == "4Tip":
                with st.form(key="level2_form"):
                    # second_level_tags = st.selectbox(
                    #     '',
                    #     [],
                    #     key='level2'
                    #     )

                    options = st.selectbox(
                        "Dispensing Tags", ["4Tip"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                            experiment step: {current_step_text}\n
                            high-level dispensing tag: 4Tip\n
                            context: {additions_prompt_level2}\n
                            return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                            the tags should be selected from the options ['Backsolvent', 'LookAhead', 'SourceTracking', 'DestinationTracking',
                            'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                            """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)

                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]
                    }

                    op1 = st.checkbox(
                        "Backsolvent", key="op1", value=op_dict["Backsolvent"]
                    )
                    op2 = st.checkbox(
                        "LookAhead", key="op2", value=op_dict["LookAhead"]
                    )
                    op3 = st.checkbox(
                        "SourceTracking", key="op3", value=op_dict["SourceTracking"]
                    )
                    op4 = st.checkbox(
                        "DestinationTracking",
                        key="op4",
                        value=op_dict["DestinationTracking"],
                    )
                    op5 = st.checkbox(
                        "StartVialTimer", key="op5", value=op_dict["StartVialTimer"]
                    )
                    op6 = st.checkbox(
                        "WaitVialTimer", key="op6", value=op_dict["WaitVialTimer"]
                    )
                    op7 = st.checkbox("Notify", key="op7", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=FourTip
                    )

            elif st.session_state.level1_option == "Powder":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["Powder"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                            experiment step: {current_step_text}\n
                            high-level dispensing tag: Powder\n
                            context: {additions_prompt_level2}\n
                            return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                            the tags should be selected from the options ['Plate','Notify'] using the above context and rules.
                            """
                    print(
                        "-----------------------------------------------------------------"
                    )

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)
                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in ["Plate", "Notify"]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False for k in ["Plate", "Notify"]
                    }
                    op1 = st.checkbox("Plate", key="op1", value=op_dict["Plate"])
                    op2 = st.checkbox("Notify", key="op2", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=Powder
                    )

        elif "set" in current_step_text.lower():
            with st.form(key="tags"):

                options = st.multiselect(
                    "", tags_values, ["Processing"], key="step_options"
                )
                submit_button_tags = st.form_submit_button(
                    label="submit tags", on_click=save_options
                )
            st.session_state.tag_counter += 1
        elif (
            "transfer" in current_step_text.lower()
            and st.session_state.level1_option is None
        ):

            if "(mg)" in current_step_text.lower():
                chem_state = "solid"
            elif "(ul)" in current_step_text.lower():
                chem_state = "liquid"
            else:
                chem_state = "liquid"

            if chem_state == "solid":
                default = "MoveVial"
            else:
                option_prompt = f"""
                    You have to decide the chemical instrument option based on the on the following criteria.
                    - chemical is water or water miscible liquid and array dim is 8x12 -> "4Tip"
                    - chemical is water or water miscible liquids and array dim is NOT 8X12 -> "SyringePump"
                    - chemical is water immiscible -> "PDT" 
                    - the whole vial is moved from one plate to another -> "MoveVial"
                    - the chemical is a powder -> "Powder"
                    chemical state is {chem_state}.
                    array dim: {st.session_state.array_dim}.
                    return only the option (one of "4Tip", "SyringePump" or "PDT", "MoveVial").
                    """

                messages = [
                    *st.session_state.chat_history,
                    {"role": "system", "content": option_prompt},
                ]
                response = completer.get_chat_completions(messages)
                assistant_response = response.choices[0].message.content
                selected_tags = []
                # check if the LLMs response is in the allowed options
                for tag in ["SyringePump", "PDT", "4Tip", "MoveVial", "Powder"]:
                    if tag in assistant_response:
                        selected_tags.append(tag)
                # if LLM does not respond with allowed responses, choose a default
                if len(selected_tags) == 0:
                    default = "SyringePump"
                else:
                    default = selected_tags[0]

            all_level1_options = ["SyringePump", "PDT", "4Tip", "MoveVial", "Powder"]
            with st.form(key="level1_form"):
                options = st.selectbox(
                    "Dispensing Tags",
                    [default] + [i for i in all_level1_options if i != default],
                    key="level1",
                )
                l1 = st.form_submit_button(
                    label="Select Main Dispensing Tag", on_click=level1
                )
        elif (
            "transfer" in current_step_text.lower()
            and st.session_state.level1_option is not None
        ):
            if st.session_state.level1_option == "SyringePump":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["SyringePump"], key="level1", disabled=True
                    )

                    second_level_tags = st.selectbox("", ["ExtSingleTip"], key="level2")

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: SyringePump\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['Backsolvent', 'LookAhead', 'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                        """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)

                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]
                    }

                    op1 = st.checkbox(
                        "Backsolvent", key="op1", value=op_dict["Backsolvent"]
                    )
                    op2 = st.checkbox(
                        "LookAhead", key="op2", value=op_dict["LookAhead"]
                    )
                    op6 = st.checkbox(
                        "StartVialTimer", key="op6", value=op_dict["StartVialTimer"]
                    )
                    op7 = st.checkbox(
                        "WaitVialTimer", key="op7", value=op_dict["WaitVialTimer"]
                    )
                    op8 = st.checkbox("Notify", key="op8", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=SyringePump
                    )
            elif st.session_state.level1_option == "PDT":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["PDT"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                            experiment step: {current_step_text}\n
                            high-level dispensing tag: PDT\n
                            context: {additions_prompt_level2}\n
                            return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                            the tags should be selected from the options ['LookAhead', 'StartVialTimer', 'WaitVialTimer','Notify', 'CapAfterDispense','NewTip'] and the available PDT size tags.
                            """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)
                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                            "ZSample",
                            "CapAfterDispense",
                            "NewTip",
                        ] + [
                            "10mLTip",
                            "1000uLTip",
                            "250uLTip" "100uLTip",
                            "50uLTip",
                            "25uLTip",
                            "10uLTip",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    size_tag = [
                        t
                        for t in options
                        if t
                        in [
                            "10mLTip",
                            "1000uLTip",
                            "250uLTip" "100uLTip",
                            "50uLTip",
                            "25uLTip",
                            "10uLTip",
                        ]
                    ]
                    if len(size_tag) == 0:
                        size_tag = "10mLTip"
                    else:
                        size_tag = size_tag[0]

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                            "ZSample",
                            "CapAfterDispense",
                            "NewTip",
                        ]
                    }

                    second_level_tags = st.selectbox(
                        "",
                        [size_tag]
                        + [
                            t
                            for t in [
                                "10mLTip",
                                "1000uLTip",
                                "250uLTip" "100uLTip",
                                "50uLTip",
                                "25uLTip",
                                "10uLTip",
                            ]
                            if t != size_tag
                        ],
                        key="level2",
                    )

                    op1 = st.checkbox(
                        "LookAhead", key="op1", value=op_dict["LookAhead"]
                    )
                    op6 = st.checkbox(
                        "CapAfterDispense", key="op6", value=op_dict["CapAfterDispense"]
                    )
                    op7 = st.checkbox("NewTip", key="op7", value=op_dict["NewTip"])
                    op8 = st.checkbox(
                        "StartVialTimer", key="op8", value=op_dict["StartVialTimer"]
                    )
                    op9 = st.checkbox(
                        "WaitVialTimer", key="op9", value=op_dict["WaitVialTimer"]
                    )
                    op10 = st.checkbox("Notify", key="op10", value=op_dict["Notify"])

                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=PDT
                    )

            elif st.session_state.level1_option == "4Tip":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["4Tip"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: 4Tip\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['Backsolvent', 'LookAhead',
                        'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                        """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)

                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False
                        for k in [
                            "Backsolvent",
                            "LookAhead",
                            "SourceTracking",
                            "DestinationTracking",
                            "Hover",
                            "StartVialTimer",
                            "WaitVialTimer",
                            "Notify",
                        ]
                    }

                    op1 = st.checkbox(
                        "Backsolvent", key="op1", value=op_dict["Backsolvent"]
                    )
                    op2 = st.checkbox(
                        "LookAhead", key="op2", value=op_dict["LookAhead"]
                    )
                    op5 = st.checkbox(
                        "StartVialTimer", key="op5", value=op_dict["StartVialTimer"]
                    )
                    op6 = st.checkbox(
                        "WaitVialTimer", key="op6", value=op_dict["WaitVialTimer"]
                    )
                    op7 = st.checkbox("Notify", key="op7", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=FourTip
                    )
            elif st.session_state.level1_option == "MoveVial":
                with st.form(key="level2_form"):

                    options = st.selectbox(
                        "Dispensing Tags", ["MoveVial"], key="level1", disabled=True
                    )

                    prompt = f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: 4Tip\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                        """

                    messages = [
                        *st.session_state.chat_history,
                        {"role": "system", "content": prompt},
                    ]
                    response = completer.get_chat_completions(messages)

                    try:
                        options = ast.literal_eval(response.choices[0].message.content)
                    except:
                        options = []
                        for opt in ["StartVialTimer", "WaitVialTimer", "Notify"]:
                            if opt in response.choices[0].message.content:
                                options.append(opt)

                    print("===options===: ", options)

                    op_dict = {
                        k: True if k in options else False
                        for k in ["StartVialTimer", "WaitVialTimer", "Notify"]
                    }

                    op5 = st.checkbox(
                        "StartVialTimer", key="op5", value=op_dict["StartVialTimer"]
                    )
                    op6 = st.checkbox(
                        "WaitVialTimer", key="op6", value=op_dict["WaitVialTimer"]
                    )
                    op7 = st.checkbox("Notify", key="op7", value=op_dict["Notify"])
                    l2 = st.form_submit_button(
                        label="Select Optional Dispensing Tags", on_click=MoveVial
                    )
        else:
            with st.form(key="tags"):

                options = st.multiselect(
                    "", tags_values, ["Processing"], key="step_options"
                )
                submit_button_tags = st.form_submit_button(
                    label="submit tags", on_click=save_options
                )
            st.session_state.tag_counter += 1

    if st.session_state.tag_counter == len(st.session_state.steps):
        with open("tag_options.pkl", "wb") as f:
            pickle.dump(st.session_state.tag_options, f)
        path2 = os.path.join(st.session_state.exp_dir, "tag_options.pkl")
        with open(path2, "wb") as f:
            pickle.dump(st.session_state.tag_options, f)

        st.session_state["tags_finalized"] = True
        st.session_state["query_experiment"] = False
