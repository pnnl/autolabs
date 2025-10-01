import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from streamlit_markdown import st_markdown


def display_chat_history():

    for msg in st.session_state.chat_history[1:]:
        # https://docs.streamlit.io/develop/api-reference/chat/st.chat_message
        # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
        if isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
            # with st.chat_message("assistant"):
            #     st_markdown(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
            # with st.chat_message("user"):
            #     st_markdown(msg.content)
        # elif isinstance(msg, SystemMessage):
        #     st.chat_message("system").write(msg.content)
        # with st.chat_message("system"):
        #     st_markdown(msg.content)

    # # for message in st.session_state.chat_history[1:]:
    # for message in st.session_state.chat_history:
    #     # if not ' tags for the ' in message['content'] and not 'Next we will determine the tags' in message['content']:
    #         with st.chat_message(message["role"]):
    #             st.markdown(message["content"])
