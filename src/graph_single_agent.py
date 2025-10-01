from typing import Annotated, Literal

from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool, StructuredTool
from langgraph.graph import START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from dotenv import load_dotenv
import os
from .config import Client
from langgraph.types import Command
from .prompts import system_prompt
import streamlit as st
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from .agents import (
    correct_vial_dims,
    refine_dict,
    refine_efficiency,
    refine_units,
    refine_delays,
)
from .agents import find_vial_array_dim, refine_plates, refine_solvents, refine_transfer
from .tools_chem import (
    get_chem_volume,
    find_chemical_amounts_in_a_solution,
    find_the_volume_corresponding_to_moles,
    find_the_concentration_of_n_percent_solution,
)
from .react_agents import (
    supervisor_node,
    understand_and_refine_node,
    chemicals_and_formats_node,
)
from .react_agents import (
    reactioons_node,
    calculation_node,
    calculation_node_without_tools,
    vial_arrangement_node,
)
from .react_agents import (
    processing_steps_node,
    final_steps_node,
    self_checks_node,
    reflection_node,
    supervisor_node_single_agent,
)
from typing import Literal
from typing_extensions import TypedDict
from .react_agents import State


completer = Client("unfiltered")
load_dotenv()


builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node_single_agent)
# builder.add_node("human_node", human_node)
# builder.add_node("Undesrand_And_Refine_Experiment", understand_and_refine_node)
# builder.add_node("Determine_Chemicals_And_Formats", chemicals_and_formats_node)
# builder.add_node("Determine_Reactions", reactioons_node)
# builder.add_node("Calculate_Chemical_Amounts_For_Reactions", calculation_node)
# builder.add_node("Determine_Vial_Organization", vial_arrangement_node)
# builder.add_node("Determine_Processing_Steps", processing_steps_node)
# builder.add_node("Generate_Final_Steps", final_steps_node)
# if st.session_state.use_self_checks:
#     builder.add_node("Self_Checks", self_checks_node)
# if st.session_state.use_reflection:
#     builder.add_node("reflection", reflection_node)

# builder.add_node("check_solvent_volume", check_solvent_volume_node)


# Compile the state graph into a runnable object
if "graph_runnable" not in st.session_state:
    st.session_state["graph_runnable"] = builder.compile(
        checkpointer=st.session_state["memory"]
    )


# graph_runnable = st.session_state['graph_runnable']
def invoke_our_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    return st.session_state["graph_runnable"].invoke(
        {"messages": st_messages},
        config={"callbacks": callables, "thread_id": "1", "recursion_limit": 30},
    )
