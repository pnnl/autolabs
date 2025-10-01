from src.inits import init

init()
import os
from dotenv import load_dotenv
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.prompts import system_prompt
from src.st_callable_util import (
    get_streamlit_cb,
)  # Utility function to get a Streamlit callback handler with context
from src.config import Client
from src.utils_streamlit import display_chat_history
import pandas as pd
from src.agents import find_vial_array_dim
import pickle
import numpy as np
from src.table import display_table
import openai
from audio_recorder_streamlit import audio_recorder
import ast
from src.utils_prompt import rewrite_prompt, switch_off_querying

# from src.create_lslibrary import get_exp_steps
from src.utils import get_exp_steps
from src.tag_utils import get_chem_state
from src.prompts import system_prompt, tags_prompt, additions_prompt_level2
from src.utils import tags_values
from langchain_openai import AzureChatOpenAI
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
import logging
import time
import evaluator
import os
import zipfile
from src.config import model

if "settings_info" in st.session_state:
    with st.sidebar:
        st.info(f"{st.session_state.settings_info}")


evaluator_name = evaluator.name
completer = Client("unfiltered")
load_dotenv()

st.session_state.streaming = False
st.session_state.timeout = None


def create_logger(results_folder):

    log_path = f"{results_folder}/main.log"
    # Set up the logger
    logger = logging.getLogger("main_logger")
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    # Create file handler with the user-specified path
    handler = logging.FileHandler(log_path, mode="w")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


st.title("AutoLabs")


def refresh_app():
    """Function to refresh the app by clearing session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


if st.button("🔄 Refresh", help="Reset the application and clear all data"):
    refresh_app()


def save_tmp_chat_history():

    results_dir = f"non-expert-evals/{st.session_state_exp_number_text}"
    with open(f"{st.session_state.eval_results_dir}/chat_history.pkl", "wb") as f:
        pickle.dump(st.session_state.chat_history, f)

    with open(f"{st.session_state.eval_results_dir}/steps.pkl", "wb") as f:
        pickle.dump(st.session_state.tmp_steps, f)

    elapsed_time = time.time() - st.session_state.start_time
    token_usage_time = {
        "Total_Tokens_Used": st.session_state.callback_handler.total_tokens,
        "Prompt_Tokens": st.session_state.callback_handler.prompt_tokens,
        "Completion_Tokens": st.session_state.callback_handler.completion_tokens,
        "Successful_Requests": st.session_state.callback_handler.successful_requests,
        "Total_Cost": st.session_state.callback_handler.total_cost,
        "elapsed_time": elapsed_time,
    }

    with open(
        f"{st.session_state.eval_results_dir}/token_usage_and_time.pkl", "wb"
    ) as f:
        pickle.dump(token_usage_time, f)


with st.sidebar:
    _ = st.button("Save Chat And Steps", on_click=save_tmp_chat_history)

display_chat_history()


def init_graph():
    from graph import Graph, SingleGraph

    st.session_state.callback_handler = OpenAICallbackHandler()

    if st.session_state.grpah_type_ma:
        _graph = Graph(
            use_self_checks=st.session_state.gpt_4o_self_checks,
            use_self_checks_reasoning=st.session_state.reasoning_self_checks,
            use_tools=st.session_state.use_tools_form_op,
        )
        _graph.build_graph()
        _graph.compile_graph()
    else:
        _graph = SingleGraph(
            use_self_checks=st.session_state.gpt_4o_self_checks,
            use_self_checks_reasoning=st.session_state.reasoning_self_checks,
            use_tools=st.session_state.use_tools_form_op,
        )
        _graph.build_graph()
        _graph.compile_graph()

    settings_folder = "MA" if st.session_state.grpah_type_ma else "SA"
    if st.session_state.use_tools_form_op == True:
        settings_folder += "-TU"
    if st.session_state.reasoning_self_checks == True:
        settings_folder += "-SCR"
    elif st.session_state.gpt_4o_self_checks == True:
        settings_folder += "-SCNR"

    st.session_state.settings_info = f"self-checks: {st.session_state.gpt_4o_self_checks}, reasoning self-checks: {st.session_state.reasoning_self_checks}, use_tools: {st.session_state.use_tools_form_op}"

    st.session_state_exp_number_text = st.session_state.exp_number
    queries = pd.read_pickle("evals/six_user_queries/original/queries.pkl")

    if st.session_state.exp_number is not None:
        query = queries[f"exp{st.session_state.exp_number[-1]}"]

    st.session_state.eval_results_dir = f"non-expert-evals/{evaluator_name}/{settings_folder}/{st.session_state_exp_number_text}"
    os.makedirs(st.session_state.eval_results_dir, exist_ok=True)
    create_logger(st.session_state.eval_results_dir)
    st.session_state.start_time = time.time()

    with st.sidebar:
        st.code(query, language=None, wrap_lines=True)


if st.session_state.iteration_count == 0:

    with st.chat_message("system"):
        st.markdown(
            "Welcome to AutoLabs. Please type the description of your experiment in the box on the left or click on the microphone icon and describe it verbaly."
        )

    st.session_state.chat_history.append(SystemMessage(system_prompt))
    st.session_state["query_experiment"] = True
    st.session_state.iteration_count += 1

    with st.chat_message("system"):
        st.markdown("Please select the relevant options:")

        with st.form(key="graph_options_form"):
            sa_ma = st.toggle("use Multi Agent", value=True, key="grpah_type_ma")
            gpt_4o_self_checks = st.toggle(
                "use Guided Self-Checks", value=False, key="gpt_4o_self_checks"
            )
            reasoning_self_checks = st.toggle(
                "use Unguided Self-Checks", value=False, key="reasoning_self_checks"
            )
            use_tools = st.toggle("use tools", value=True, key="use_tools_form_op")

            exp_option = st.selectbox(
                "Select the experiment number.",
                ("Exp1", "Exp2", "Exp3", "Exp4", "Exp5"),
                index=None,
                placeholder="Select experiment",
                key="exp_number",
            )

            submit_graph_form = st.form_submit_button(
                label="Submit", on_click=init_graph
            )


if st.session_state["query_experiment"] == True:
    from graph import invoke_our_graph

    with st.sidebar:
        user_prompt = st.chat_input("describe your experiment....")

    # Handle user input if provided
    if user_prompt:
        st.chat_message("user").write(user_prompt)
        st.session_state.chat_history.append(HumanMessage(user_prompt))

        if st.session_state.rewrite_user_query:
            with st.sidebar:
                st.info("Rewriting the user query.")

            if len(user_prompt) > 150:
                st.session_state.chat_history.append(
                    SystemMessage("Rewriting the user query improving it's clarity.")
                )
                resp = model.invoke(
                    [
                        SystemMessage(
                            f"""Review the user's query and identify any ambiguities or missing details. Rewrite the query for maximum clarity and completeness, ensuring the original intent is preserved.
                                                
                                            user query: {user_prompt}
                                            """
                        )
                    ]
                )
                st.session_state.chat_history.append(
                    SystemMessage(
                        f"""Use this rewritten version of the user query to determine experiment steps.
                                                                
                                                                {resp.content}
                                                                """
                    )
                )

        with st.chat_message("assistant"):

            st_callback = get_streamlit_cb(st.container())
            callback = [st_callback]

            response = invoke_our_graph(st.session_state.chat_history, callback)

            assistant_response = response["messages"][-1].content

            if (
                assistant_response
                and "<final-steps>" in assistant_response
                and "</final-steps>" in assistant_response
            ):

                st.session_state.current_steps_text = assistant_response
                st.session_state.current_steps = pd.DataFrame(
                    get_exp_steps(assistant_response)
                )
                st.session_state.tmp_steps = get_exp_steps(assistant_response)
                with st.sidebar:
                    st.info(f"final steps: {type(st.session_state.current_steps)}")

            if assistant_response:
                st.session_state.chat_history.append(AIMessage(assistant_response))
                st.markdown(assistant_response)


display_table()

if st.session_state.current_steps is not None:
    st.session_state.use_current_steps = st.button(
        "Use Current Steps", on_click=switch_off_querying
    )


from src.tags import process_tags

if st.session_state["work_on_optional_tags"] == True:

    process_tags()


with st.sidebar:
    st.markdown("tag counter:" + str(st.session_state.tag_counter))

    def create_lsr_file():
        file_content = create_xml("current_steps.pkl", "tag_options.pkl", completer)
        with open("exp.xml", "w") as file:
            file.write(file_content)
            file.write("\n")

        path2 = os.path.join(st.session_state.exp_dir, "exp.xml")
        with open(path2, "w") as file:
            file.write(file_content)
            file.write("\n")

        with open("exp.lsr", "w") as file:
            file.write(file_content)
            file.write("\n")

        path2 = os.path.join(st.session_state.exp_dir, "exp.lsr")
        with open(path2, "w") as file:
            file.write(file_content)
            file.write("\n")

    ## We are turning off LSR creation
    # TURN_OFF_LSR=True
    # if not TURN_OFF_LSR:
    creta_lsr_fle_button = st.button("Create LSR", on_click=create_lsr_file)
    if creta_lsr_fle_button:
        # os.system(f'cp exp.xml {st.session_state.exp_dir}/')
        # os.system(f'cp exp.lsr {st.session_state.exp_dir}/')
        # subprocess.call(f'copy exp.xml {st.session_state.exp_dir}/', shell=True)
        # subprocess.call(f'copy exp.lsr {st.session_state.exp_dir}/', shell=True)

        path2 = os.path.join(st.session_state.exp_dir, "chat_history.pkl")
        with open(path2, "wb") as f:
            pickle.dump(st.session_state.chat_history, f)
        st.markdown("LSR file created. File names: exp.xml, exp.lsr")

with st.sidebar:
    if os.path.exists("exp.lsr"):
        with open("exp.lsr", "rb") as file:
            xml_data = file.read()

        st.download_button(
            label="Download LSR File",
            data=xml_data,
            file_name="downloaded_LSR.lsr",
            mime="application/xml",
        )


def zip_directory(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Store files with a relative path inside the zip
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, arcname)
            # Optionally, add empty directories by writing them to the zip
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                arcname = os.path.relpath(dir_path, os.path.dirname(folder_path))
                zipf.write(dir_path, arcname)


with st.sidebar:
    zip_directory("non-expert-evals", "non_expert_evals.zip")

    with open("non_expert_evals.zip", "rb") as fp:
        st.download_button(
            label="Download Evaluations",
            data=fp,
            file_name="non_expert_evals.zip",
            mime="application/zip",
        )
