import streamlit as st
import numpy as np
import ast
import pickle
from .tag_utils import SyringePump, PDT, FourTip, Powder, get_chem_state
from .prompts import additions_prompt_level2, tags_prompt
from langchain_core.messages import SystemMessage
import os


def handle_optional_tags(model):
    if st.session_state.tag_counter < len(st.session_state.steps):
        i = st.session_state.tag_counter
        st.session_state.step_text = st.session_state.steps[i].get_text()

        current_step_text = st.session_state.step_text
        current_step_text_loc = current_step_text.find("{")
        current_step_text = current_step_text[:current_step_text_loc]

        with st.chat_message("system"):
            message = f"Please make corrections to the suggested tags for the {current_step_text} step?"
            st.markdown(message)

        if st.session_state.tag_counter == 0:
            message_init = f"{tags_prompt}"
            st.session_state.chat_history.append(SystemMessage(message_init))

        # Add logic for handling different cases (e.g., "add", "set", "transfer")
        # Example for "add":
        if (
            "add" in current_step_text.lower()
            and st.session_state.level1_option is None
        ):
            chem_name, _chem_state = get_chem_state(model, current_step_text)

            if "(mg)" in current_step_text.lower():
                chem_state = "solid"
            elif "(ul)" in current_step_text.lower():
                chem_state = "liquid"
            else:
                chem_state = _chem_state

            if chem_state == "solid":
                default = "Powder"
            else:
                default = "SyringePump"  # Default logic for liquids

            all_level1_options = ["Powder", "SyringePump", "PDT", "4Tip"]
            with st.form(key="level1_form"):
                options = st.selectbox(
                    "Dispensing Tags",
                    [default] + [i for i in all_level1_options if i != default],
                    key="level1",
                )
                l1 = st.form_submit_button(label="Select Main Dispensing Tag")

        # Add other cases like "set", "transfer", etc.

        st.session_state.tag_counter += 1

    if st.session_state.tag_counter == len(st.session_state.steps):
        with open("tag_options.pkl", "wb") as f:
            pickle.dump(st.session_state.tag_options, f)
        path2 = os.path.join(st.session_state.exp_dir, "tag_options.pkl")
        with open(path2, "wb") as f:
            pickle.dump(st.session_state.tag_options, f)

        st.session_state["tags_finalized"] = True
        st.session_state["query_experiment"] = False


def optional_tags_logic():
    if st.session_state["work_on_optional_tags"] == True:
        if st.session_state.tag_counter < len(st.session_state.steps):
            i = st.session_state.tag_counter
            st.session_state.step_text = st.session_state.steps[i].get_text()

            current_step_text = st.session_state.step_text
            current_step_text_loc = current_step_text.find("{")
            current_step_text = current_step_text[:current_step_text_loc]

            with st.chat_message("system"):
                message = f"Please make corrections to the suggested tags for the {current_step_text} step?"
                st.markdown(message)

            if st.session_state.tag_counter == 0:
                message_init = f"{tags_prompt}"
                st.session_state.chat_history.append(SystemMessage(message_init))

            # Add logic for handling different cases (e.g., "add", "set", "transfer")
            # Example for "add":
            if (
                "add" in current_step_text.lower()
                and st.session_state.level1_option is None
            ):
                chem_name, _chem_state = get_chem_state(None, current_step_text)

                if "(mg)" in current_step_text.lower():
                    chem_state = "solid"
                elif "(ul)" in current_step_text.lower():
                    chem_state = "liquid"
                else:
                    chem_state = _chem_state

                if chem_state == "solid":
                    default = "Powder"
                else:
                    default = "SyringePump"  # Default logic for liquids

                all_level1_options = ["Powder", "SyringePump", "PDT", "4Tip"]
                with st.form(key="level1_form"):
                    options = st.selectbox(
                        "Dispensing Tags",
                        [default] + [i for i in all_level1_options if i != default],
                        key="level1",
                    )
                    l1 = st.form_submit_button(label="Select Main Dispensing Tag")

            # Add other cases like "set", "transfer", etc.

            st.session_state.tag_counter += 1

        if st.session_state.tag_counter == len(st.session_state.steps):
            with open("tag_options.pkl", "wb") as f:
                pickle.dump(st.session_state.tag_options, f)
            path2 = os.path.join(st.session_state.exp_dir, "tag_options.pkl")
            with open(path2, "wb") as f:
                pickle.dump(st.session_state.tag_options, f)

            st.session_state["tags_finalized"] = True
            st.session_state["query_experiment"] = False
