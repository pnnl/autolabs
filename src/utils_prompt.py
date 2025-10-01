import streamlit as st
import pickle
import os
from src.agents import find_vial_array_dim

# from src.create_lslibrary import create_xml, get_exp_steps
from src.utils import get_exp_steps
from src.config import Client
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.config import model

completer = Client("unfiltered")

# model = AzureChatOpenAI(
#     model='gpt-4o',
#     temperature=0.0,
#     streaming=True,
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#     api_version="2024-05-01-preview",
#     azure_endpoint="https://autolabs.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
# )


def rewrite_prompt(prompt, completer):

    messages = [
        {
            "role": "system",
            "content": "rewrite the following user prompt in a llm-friendly way",
        },
        {"role": "user", "content": prompt},
    ]
    response = completer.get_chat_completions(messages)
    assistant_response = response.choices[0].message.content

    return assistant_response


def save_steps():
    array_dim = find_vial_array_dim(st.session_state.chat_history, model)
    st.session_state.array_dim = array_dim
    final_steps_message = st.session_state.chat_history[-1].content
    if (
        "<final-steps>" in final_steps_message
        and "</final-steps>" in final_steps_message
    ):
        with open("current_steps.pkl", "wb") as f:
            pickle.dump({"steps": final_steps_message, "array_dim": array_dim}, f)
        path2 = os.path.join(st.session_state.exp_dir, "current_steps.pkl")
        with open(path2, "wb") as f:
            pickle.dump({"steps": final_steps_message, "array_dim": array_dim}, f)
        # os.system(f'cp current_steps.pkl {st.session_state.exp_dir}/')
        # subprocess.call(f'copy current_steps.pkl {st.session_state.exp_dir}/', shell=True)


def switch_off_querying():

    # st.session_state["query_experiment"] = False
    st.session_state["work_on_optional_tags"] = True
    save_steps()
    # steps = st.session_state.chat_history[-1]
    steps = st.session_state.current_steps_text
    print("steps: ", steps)
    # st.session_state.steps = get_exp_steps(steps.content)
    st.session_state.steps = get_exp_steps(steps)

    with st.chat_message("system"):
        message = "Ok, Now let's work on the tags."
        st.markdown(message)
        # st.session_state.chat_history.append({"role": "system", "content": message})
