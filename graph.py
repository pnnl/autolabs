from langgraph.graph import START, StateGraph
import streamlit as st
from langgraph.graph import StateGraph, START
import streamlit as st
from src.inits import init
from src.inits import init_graph_variables
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

init()

# NOTE: Set this to True when needed to stream the output
st.session_state.streaming = False


class Graph:

    def __init__(self, use_self_checks, use_self_checks_reasoning, use_tools):
        self.use_self_checks = use_self_checks
        self.use_self_checks_reasoning = use_self_checks_reasoning
        self.use_tools = use_tools
        self.use_reflection = False
        self.redo_calculations = False

        # init_graph_variables(use_self_checks=self.use_self_checks, use_self_checks_reasoning=self.use_self_checks_reasoning,
        #                      use_tools=self.use_tools)
        init_graph_variables(
            use_self_checks=self.use_self_checks,
            use_self_checks_reasoning=self.use_self_checks_reasoning,
            use_tools=self.use_tools,
            use_reflection=self.use_reflection,
            redo_calculations=self.redo_calculations,
        )

    def build_graph(self):
        # from src.react_agents import State
        # from src.react_agents import supervisor_node, understand_and_refine_node, chemicals_and_formats_node
        # from src.react_agents import reactioons_node, calculation_node, vial_arrangement_node
        # from src.react_agents import processing_steps_node, final_steps_node, self_checks_node

        # builder = StateGraph(State)
        # builder.add_edge(START, "supervisor")
        # builder.add_node("supervisor", supervisor_node)
        # # builder.add_node("human_node", human_node)
        # builder.add_node("Undesrand_And_Refine_Experiment", understand_and_refine_node)
        # builder.add_node("Determine_Chemicals_And_Formats", chemicals_and_formats_node)
        # builder.add_node("Determine_Reactions", reactioons_node)
        # builder.add_node("Calculate_Chemical_Amounts_For_Reactions", calculation_node)
        # builder.add_node("Determine_Vial_Organization", vial_arrangement_node)
        # builder.add_node("Determine_Processing_Steps", processing_steps_node)
        # builder.add_node("Generate_Final_Steps", final_steps_node)
        # # if st.session_state.use_self_checks:
        # builder.add_node("Self_Checks", self_checks_node)
        # # builder.add_node("Self_Checks_Reasoning", self_checks_with_reasoning_node)
        # # if st.session_state.use_reflection:
        # #     builder.add_node("reflection", reflection_node)

        # # graph = builder.compile()
        # # builder.add_node("check_solvent_volume", check_solvent_volume_node)

        # self.graph = builder

        from src.react_agents import (
            supervisor_node,
            understand_and_refine_node,
            chemicals_and_formats_node,
        )
        from src.react_agents import reactioons_node, vial_arrangement_node
        from src.react_agents import (
            processing_steps_node,
            final_steps_node,
            calculation_node,
        )
        from src.react_agents import (
            self_checks_node,
            self_checks_with_reasoning_node,
            reflection_node,
        )
        from langgraph.graph import StateGraph, START
        from src.react_agents import State

        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("Understand_And_Refine_Experiment", understand_and_refine_node)
        # builder.add_node("Determine_Chemicals_And_Formats", chemicals_and_formats_node)
        # builder.add_node("Determine_Reactions", reactioons_node)
        builder.add_node("Calculate_Chemical_Amounts_For_Reactions", calculation_node)
        builder.add_node("Determine_Vial_Organization", vial_arrangement_node)
        builder.add_node("Determine_Processing_Steps", processing_steps_node)
        builder.add_node("Generate_Final_Steps", final_steps_node)
        if self.use_self_checks:
            builder.add_node("Self_Checks", self_checks_node)
        if self.use_self_checks_reasoning:
            builder.add_node("Self_Checks_Reasoning", self_checks_with_reasoning_node)
        if self.use_reflection:
            builder.add_node("reflection", reflection_node)

        self.graph = builder

    # st.session_state.callback_handler = OpenAICallbackHandler()

    # Compile the state graph into a runnable object
    def compile_graph(self):
        # if 'graph_runnable' not in st.session_state:
        st.session_state["graph_runnable"] = self.graph.compile(
            checkpointer=st.session_state["memory"]
        )


# graph_runnable = st.session_state['graph_runnable']
def invoke_our_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    # using both streamlit callback handler and openai's
    return st.session_state["graph_runnable"].invoke(
        {"messages": st_messages},
        config={
            "callbacks": callables + [st.session_state.callback_handler],
            "thread_id": "1",
            "recursion_limit": 30,
        },
    )

    # only use openai's
    # return st.session_state['graph_runnable'].invoke({"messages": st_messages}, config={"callbacks": [st.session_state.callback_handler], "thread_id": "1", 'recursion_limit': 30})


# Compile the state graph into a runnable object
# graph_runnable = builder.compile()
# def invoke_our_graph(st_messages, callables):
#     if not isinstance(callables, list):
#         raise TypeError("callables must be a list")
#     return graph_runnable.invoke({"messages": st_messages}, config={"callbacks": callables, 'recursion_limit': 30})


class SingleGraph:

    def __init__(self, use_self_checks, use_self_checks_reasoning, use_tools):
        self.use_self_checks = use_self_checks
        self.use_self_checks_reasoning = use_self_checks_reasoning
        self.use_tools = use_tools
        self.use_reflection = False
        self.redo_calculations = False

        init_graph_variables(
            self.use_self_checks,
            use_self_checks_reasoning=self.use_self_checks_reasoning,
            use_tools=self.use_tools,
            use_reflection=self.use_reflection,
            redo_calculations=self.redo_calculations,
        )

    def build_graph(self):

        from langgraph.graph import StateGraph, START
        from src.react_agents import State
        from src.react_agents import supervisor_node_single_agent

        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", supervisor_node_single_agent)

        self.graph = builder

        # Compile the state graph into a runnable object

    def compile_graph(self):
        # if 'graph_runnable' not in st.session_state:
        st.session_state["graph_runnable"] = self.graph.compile(
            checkpointer=st.session_state["memory"]
        )
