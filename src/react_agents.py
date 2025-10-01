from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import AzureChatOpenAI
from .prompts import system_prompt, system_prompt_single_agent
# from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
import streamlit as st
from .tools_chem import get_chem_volume, find_chemical_amounts_in_a_solution, find_the_volume_corresponding_to_moles, find_the_concentration_of_n_percent_solution, find_stock_solution_volume_corresponding_to_a_modifier
from .agents import refine_units, refine_efficiency, refine_delays, refine_plates, refine_solvents, refine_transfer, refine_additions
import os
from langgraph.prebuilt import ToolNode
from openevals.llm import create_llm_as_judge
import logging
from .config import model
logger = logging.getLogger('main_logger')
logger.info(f'at react_agents - streamin = {st.session_state.streaming}')
load_dotenv()


llm_gp4o=model
llm_o3_low=model
llm_o3_medium=model
# llm_gp4o = AzureChatOpenAI(
#     model='gpt-4o',
#     temperature=0.0,
#     streaming=st.session_state.streaming,
#     max_tokens=None,
#     timeout=st.session_state.timeout,
#     # max_retries=2,
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
#     api_version="2024-08-01-preview",
#     azure_endpoint="https://autolabs.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
# )



# llm_o3_low = AzureChatOpenAI(
#     model="o3-mini",
#     reasoning_effort="low",
#     streaming=st.session_state.streaming,
#     max_tokens=None,
#     timeout=st.session_state.timeout,
#     api_key=os.getenv("AZURE_OPENAI_API_REASONING_KEY"),  
#     api_version="2024-12-01-preview",
#     azure_endpoint="https://autolabs-reasoning.openai.azure.com/openai/deployments/o3-mini/chat/completions?api-version=2024-12-01-preview"
# )


# llm_o3_medium = AzureChatOpenAI(
#     model="o3-mini",
#     reasoning_effort="medium",
#     streaming=st.session_state.streaming,
#     max_tokens=None,
#     timeout=st.session_state.timeout,
#     api_key=os.getenv("AZURE_OPENAI_API_REASONING_KEY"),  
#     api_version="2024-12-01-preview",
#     azure_endpoint="https://autolabs-reasoning.openai.azure.com/openai/deployments/o3-mini/chat/completions?api-version=2024-12-01-preview"
# )



class State(MessagesState):
    next: str
    checked_units: bool = False

# the supervisor agent for the single agent case
def supervisor_node_single_agent(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the supervisor_node_single_agent')
    messages = [
        SystemMessage(system_prompt_single_agent),
    ] + state["messages"]
    
    
    if st.session_state.use_tools:
        logger.info('using tools - single node ')
        llm_with_tools = llm_o3_medium.bind_tools(chem_tools_list)
        assistant_response = llm_with_tools.invoke(messages)
        st.session_state.chat_history.append(assistant_response)

        while len(assistant_response.tool_calls)!=0:
            with st.sidebar:
                st.markdown(f'invoking tools')
            for tool_call in assistant_response.tool_calls:
                logger.info(f'making tool calls  - tool call id: {tool_call["id"]}')
                logger.info(f'making tool calls  - tool call: {str(tool_call)}')

                selected_tool = chem_tools_dict[tool_call["name"].lower()]
                tool_output = selected_tool.invoke(tool_call["args"])
                st.session_state.chat_history.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))


            assistant_response = llm_with_tools.invoke(st.session_state.chat_history)
            st.session_state.chat_history.append(assistant_response)

        result = assistant_response.content
    else:
        result = llm_o3_medium.invoke(messages)
        result = result.content



    if "<final-steps>" in result and  '</final-steps>' in result:

        if st.session_state.use_self_checks:

            logger.info('single agent - non-reasoning, individual self checks.')

            messages = state['messages']
            result = do_self_checks(messages, llm_gp4o)
            result = result.content
            st.session_state.self_checks_done = True

        elif st.session_state.use_self_checks_reasoning:
            logger.info('single agent - reasoning self checks.')

            messages = state['messages']
            assistant_response = result

            result = do_self_checks_reasoning(messages, assistant_response)
            st.session_state.self_checks_done = True

        # else:
        #     return Command(
        #             update={
        #                 "messages": [
        #                     AIMessage(content=result, name="supervisor")
        #                 ]
        #             },
        #             goto="__end__",
        #         )

    return Command(
            update={
                "messages": [
                    AIMessage(content=result, name="supervisor")
                ]
            },
            goto="__end__",
        )

members = ["Understand_And_Refine_Experiment",
        #    "Determine_Chemicals_And_Formats",
           # "human_node"
        #   "Determine_Reactions",
          "Calculate_Chemical_Amounts_For_Reactions",
           "Determine_Vial_Organization",
           "Determine_Processing_Steps",
           "Generate_Final_Steps",
          ]

if st.session_state.use_self_checks==True:
    print('#### Using Self Checks ####')
    members += ["Self_Checks"]

if st.session_state.use_self_checks_reasoning==True:
    members += ["Self_Checks_Reasoning"]

options = members + ["FINISH"]

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

class Compare_Calculations(TypedDict):
    """Compare if the two results are the same. If so, return yes. Else return no."""

    result: Literal['yes', 'no']


class YesNo(TypedDict):
    """Return either yes or no."""

    result: Literal['yes', 'no']

# the supervisor agent for the multi agent case
def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    """
    The supervisor node has the option to delegate tasks to any other member.
    """
    st.sidebar.write('At the multi agent supervisor_node')
    logger.info('At the supervisor node')
    messages = [
        SystemMessage(system_prompt),
    ] + state["messages"]
    
    response = llm_gp4o.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})



    
def do_self_checks(messages, llm):
    logger.info('self_check: refine_efficiency')
    _, assistant_response = refine_efficiency(messages, llm)
    messages.append(assistant_response)

    logger.info('self_check: refine_units')
    _, assistant_response = refine_units(messages, llm)
    messages.append(assistant_response)

    logger.info('self_check: refine_delays')
    _, assistant_response = refine_delays(messages, llm)
    messages.append(assistant_response)

    logger.info('self_check: refine_plates')
    _, assistant_response = refine_plates(messages, llm)
    messages.append(assistant_response)

    logger.info('self_check: refine_solvents')
    _, assistant_response = refine_solvents(messages, llm)
    messages.append(assistant_response)

    logger.info('self_check: refine_transfer')
    _, assistant_response = refine_transfer(messages, llm)
    # messages.append(assistant_response)

    logger.info('self_check: refine_additions')
    _, assistant_response = refine_additions(messages, llm)

    result = assistant_response 

    return result


def self_checks_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the self_checks_node')
    # print("#### Using Self Checks ####")
    with st.sidebar:
        st.markdown("At the self checks node")

    messages = state['messages']
    assistant_response = do_self_checks(messages, llm_gp4o)
    st.session_state.self_checks_done = True
    
    return Command(
        update={
            "messages": [
                AIMessage(content=assistant_response.content, name="Self_Checks")
            ],
        },
        goto="__end__",
    )


from .self_check import validate
def self_checks_with_reasoning_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the self_checks_with_reasoning_node')

    messages = state['messages'][:-1]
    assistant_response = state['messages'][-1].content

    # assert 'final-steps' in assistant_response

    with st.sidebar:
        st.markdown('At the self checks reasoning node')

    assistant_response = do_self_checks_reasoning(messages,assistant_response)
    st.session_state.self_checks_done = True
    # modify = True
    # valid_count = 0
    # chat_history = messages
    # while modify and valid_count < 10:
    #     print('valid count', valid_count)
    #     modify, reasoning, assistant_response = validate(chat_history, assistant_response)
    #     # chat_history[-1]['role'] = 'assistant'
    #     chat_history[-1].type = 'ai'
    #     chat_history[-1].content = chat_history[-1].content.replace('<final-steps>','').replace('</final-steps>','')
    #     chat_history.append(AIMessage(reasoning))
    #     chat_history.append(AIMessage(assistant_response))
    #     # st.session_state.current_steps = pd.DataFrame(get_exp_steps(assistant_response))
    #     valid_count += 1

    return Command(
        update={
            "messages": [
                AIMessage(content=assistant_response, name="Self_Checks_Reasoning")
            ],
        },
        goto="__end__",
    )


def do_self_checks_reasoning(messages, assistant_response):

    logger.info('Working on do_self_checks_reasoning.')
    modify = True
    valid_count = 0
    chat_history = messages
    while modify and valid_count < 5:
        print('valid count', valid_count)
        logger.info(f'reasoning iteration {valid_count}')
        modify, reasoning, assistant_response = validate(chat_history, assistant_response)
        # chat_history[-1]['role'] = 'assistant'
        chat_history[-1].type = 'ai'
        chat_history[-1].content = chat_history[-1].content.replace('<final-steps>','').replace('</final-steps>','')
        chat_history.append(AIMessage(reasoning))
        chat_history.append(AIMessage(assistant_response))
        # st.session_state.current_steps = pd.DataFrame(get_exp_steps(assistant_response))
        valid_count += 1
    logger.info('self check using the reasoning model is finished.')

    return assistant_response

#--------------------------------------
# Undesrand_And_Refine_Experiment_agent
#--------------------------------------
Undesrand_And_Refine_Experiment_agent = create_react_agent(
    llm_o3_medium, tools = [], prompt="""Your role is to understand, refine and correct experimental steps according to user instructions. 
    Confirm with the user the agent's understanding of the experiment and source chemicals. 
    Specially, if there are any part in the descrition that you are confused about, ask for clarification.
    If you have a doubt about whether a chemical is pure or pre-diluted (n% A in B), ALWAYS get this confirmed from the user.
    If a modifier or chemical is provided as a pre-diluted solution, for example 3% A in B, this means that 3 parts of pure A is in 100 parts of the solution.
"""
)
def understand_and_refine_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the understand_and_refine_node')
    with st.sidebar:
        st.markdown("At the understanding and refineing step.")

        ##If we are using the processing steps RAG, we will invoke it here.
    if st.session_state.use_processing_steps_rag:
        logger.info('Using processing steps RAG. understand_and_refine_node')
        from .rag import processing_steps_rag
        step_context = processing_steps_rag(st.session_state.user_prompt)
        
        state["messages"].append(SystemMessage(f"Below are some experiment objectives and corresponding steps from past experiment for reference. Use them to determine the processing steps for the current experiment. \n\n {step_context}"))
         

    result = Undesrand_And_Refine_Experiment_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result, "Undesrand_And_Refine_Experiment")

    
    node = "Understand_And_Refine_Experiment"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )

    if st.session_state.use_reflection:
        logger.info('Using reflections')
        return Command(
            update={
                "messages": [
                    AIMessage(content=result["messages"][-1].content, name="Undesrand_And_Refine_Experiment")
                ]
            },
            goto="reflection",
        )
    else:
        logger.info('Not using reflections')
        return Command(
            update={
                "messages": [
                    AIMessage(content=result["messages"][-1].content, name="Undesrand_And_Refine_Experiment")
                ]
            },
            goto="__end__",
        )

#----------------
# reflection_node
#----------------
def reflection_node(state: State) -> Command[Literal["__end__","Undesrand_And_Refine_Experiment"]]:
    logger.info('At the reflection_node')
    with st.sidebar:
        st.markdown("At the reflection node")

    common_critique_prompt= """You are an expert chemist. You have to evaluate an experiment description for clarity. Check whether you undersrand the composition of chemical mixtures.
    The description will be used by an llm to generate experiment steps. Therefore, the description should
    be clear so that the correct calculations have to be done. You will be provided a chat history containing the description. First, identify the description of the experiment.
    """
    critique_prompt=common_critique_prompt + """If the description is not clear enough, respond with 'no'.
    If it is sufficiently clear, respond with 'yes'.
"""

    critique_prompt2=common_critique_prompt+"""If the description is not clear, come up with recommendations to improve clarity.
"""

    messages = state['messages']
   
    # evaluator = create_llm_as_judge(
    #     prompt=critique_prompt,
    #     # model="openai:o3-mini",
    #     judge=llm_reasoning,
    #     feedback_key="pass",
    # )
    

    # resp = llm.with_structured_output(YesNo).invoke(messages+[HumanMessage(critique_prompt)])
    resp = llm_o3_low.with_structured_output(YesNo).invoke([SystemMessage(critique_prompt)] + [SystemMessage("The entire chat history is as follows:")] + messages)

    # eval_result = evaluator(outputs=state["messages"][-1].content, inputs=None)
    eval_result = resp['result']
    logger.info(f'eval_result: {eval_result}')

    if eval_result =='yes' or st.session_state.reflection_count>1:
        # if the description is clear or reflection count is greater than 1, no reflections will be done.
        logger.info(f'st.session_state.reflection_count: {st.session_state.reflection_count}')
        return Command(
            update={
                "messages": [
                    AIMessage(content=state['messages'][-1].content, name="Reflection")
                ],
            },
            goto="__end__",
        )
    else:
        st.session_state.reflection_count+=1
        with st.sidebar:
            st.info(f'number of time the reflection node is visited {st.session_state.reflection_count}')
        logger.info(f'number of time the reflection node is visited {st.session_state.reflection_count}')
        if st.session_state.reflection_count==2:
            st.session_state.use_reflection = False

        resp = llm_o3_medium.invoke(messages+[HumanMessage(critique_prompt2)])
        return Command(
            update={
                "messages": [
                    HumanMessage(content=resp.content, name="Reflection")
                ],
            },
            goto="Undesrand_And_Refine_Experiment",
        )

#-------------------------------------
# Determine_Chemicals_And_Format_agent
#-------------------------------------
Determine_Chemicals_And_Format_agent = create_react_agent(
    llm_o3_medium, tools=[], prompt="""Your role is to determine available source chemicals and their formats. For example the chemicals may be solids, 
    liquid, mixtures, or solutions. Do not do the calculations yet."""
)

def chemicals_and_formats_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At chemicals_and_formats_node')
    with st.sidebar:
        st.markdown("At the chemicals step.")


    result = Determine_Chemicals_And_Format_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result, "Determine_Chemicals_And_Formats")
    node = "Determine_Chemicals_And_Formats"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )

    logger.info(f'output from reactions node: {result["messages"][-1].content}')
    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"][-1].content, name="Determine_Chemicals_And_Formats")
            ]
        },
        goto="__end__",
    )
#--------------------------
# Determine_Reactions_agent
#--------------------------
Determine_Reactions_agent = create_react_agent(
    llm_o3_medium, tools=[], prompt="""Your role is to determine which reactions, mixtures, or solutions will be performed. 
    (do not perform calculations yet)."""
)
def reactioons_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At reactioons_node')

    with st.sidebar:
        st.markdown("At the reactions step.")
    result = Determine_Reactions_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result, "Determine_Reactions")
    node = "Determine_Reactions"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )


    logger.info(f'output from reactions node: {result["messages"][-1].content}')
    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"][-1].content, name="Determine_Reactions")
            ]
        },
        goto="__end__",
    )


#---------------------------
# Chemical Calculations Node
#---------------------------
chem_tools_list = [get_chem_volume, find_the_volume_corresponding_to_moles, find_the_concentration_of_n_percent_solution, find_chemical_amounts_in_a_solution
                   ]
#    find_stock_solution_volume_corresponding_to_a_modifier
chem_tools_dict = {ct.func.__name__: ct for ct in chem_tools_list}

def calculation_node(state: State) -> Command[Literal["__end__"]]:
    logger.info(f'At calculation_node. Using tools = {st.session_state.use_tools}')
    with st.sidebar:
        st.markdown("At the Calculate_Chemical_Amounts_For_Reactions step.")
    current_messages = len(state['messages'])

    if st.session_state.use_tools:
        calculation_prompt = """Your role is to calculate the amounts of each chmeical required for for each reaction or mixture.
        This is a very important step. Pay extra care. Assume the role of a experienced syntheric chemist.
        Note that when calculating the solvent volume, you have to take into account the volumes of all the other chemicals in the solution.
        Make use of the attached tools to do calculations as neccessary.
        """
        tools = chem_tools_list
    else:
        calculation_prompt = """Your role is to calculate the amounts of each chmeical required for for each reaction or mixture.
        This is a very important step. Pay extra care. Assume the role of a experienced syntheric chemist.
        Note that when calculating the solvent volume, you have to take into account the volumes of all the other chemicals in the solution.
        """
        tools = []


    logger.info(f'calculation prompt: {calculation_prompt}')
    logger.info(f'tools: {tools}')

    Calculate_Chemical_Amounts_For_Reactions_agent = create_react_agent(
    llm_o3_medium, tools=tools, 
    prompt=calculation_prompt
)

    result = Calculate_Chemical_Amounts_For_Reactions_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result, "Calculate_Chemical_Amounts_For_Reactions")
    node = "Calculate_Chemical_Amounts_For_Reactions"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )


    tool_messages=[]
    for msg in result['messages'][current_messages:]:
        if hasattr(msg, 'tool_call_id') or hasattr(msg, 'tool_calls') :
            print(msg)
            tool_messages.append(msg)
            st.session_state.chat_history.append(msg)
            logger.info(f'tool message: {msg}')


    if st.session_state.redo_calculations and st.session_state.n_redone < 2:
        logger.info(f'Redoing calculations - with tools. n_redone = {st.session_state.n_redone}')

        with st.sidebar:
            st.info('double checking the calculations')
        result2 = Calculate_Chemical_Amounts_For_Reactions_agent.invoke(state)
        st.session_state.n_redone += 1


        messages = f"""You are an expert chemist. Determine whether these two results are the same.
        
        result1: {result["messages"][-1].content}
        
        result2: {result2["messages"][-1].content}
"""
        output = llm_o3_medium.with_structured_output(Compare_Calculations).invoke(messages)
        
        if output['result'] == 'yes':
            return Command(
                update={
                    "messages": tool_messages + [
                AIMessage(content=result["messages"][-1].content, name="Calculate_Chemical_Amounts_For_Reactions")
                ]
            },
            goto="__end__",
            )
        else:
            return Command(
                update={
                    "messages": [HumanMessage(content="How did you do the calculations? Can you rethink about the calculations and tools you selected?", name="Calculate_Chemical_Amounts_For_Reactions")]
            },
            goto="supervisor",
            )

    return Command(
        update={
            "messages": tool_messages + [
                AIMessage(content=result["messages"][-1].content, name="Calculate_Chemical_Amounts_For_Reactions")
            ]
        },
        
        goto="__end__",
    )

#----------------------------------
# Determine_Vial_Organization_agent
#----------------------------------
Determine_Vial_Organization_agent = create_react_agent(
    llm_o3_medium, tools=[], prompt="""Your role is to determine which chemicals should be added to
     which vials. Note that there could be cases where multiple plates are involved.
     Add each input chemical using as few steps as possible. Show the amounts in different
     vials in a markdown table like below.

     |vial| chem1 name| chem2 name|
     |----|-----------|------------|
     |A1| chem1 value in A1 | chem 2 value in A1|
     |B1| chem1 value in B1 | chem 2 value in B1|
    """
)
def vial_arrangement_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the vial_arrangement_node')
    with st.sidebar:
        st.markdown("At the vial arrangement step.")
    result = Determine_Vial_Organization_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result,"Determine_Vial_Organization")
    node = "Determine_Vial_Organization"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )
        
    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"][-1].content, name="Determine_Vial_Organization")
            ]
        },
        goto="__end__",
    )

#---------------------------------
# Determine_Processing_Steps_agent
#---------------------------------
Determine_Processing_Steps_agent = create_react_agent(
    llm_o3_medium, tools=[], prompt="""Your role is to determine determine the additional processing steps needed.
    For example, heating, stirring, delay, etc.
    """
)
def processing_steps_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the processing_steps_node')

    with st.sidebar:
        st.markdown("At the processing steps_node.")

    ##If we are using the processing steps RAG, we will invoke it here.
    # if st.session_state.use_processing_steps_rag:
    #     logger.info('Using processing steps RAG')
    #     from .rag import processing_steps_rag
    #     step_context = processing_steps_rag.invoke(st.session_state.user_prompt)
        
    #     state["messages"].append(SystemMessage(f"Below are some experiment objectives and corresponding steps from past experiment for reference. Use them to determine the processing steps for the current experiment. \n\n {step_context}"))
         

    result = Determine_Processing_Steps_agent.invoke(state)
    # TODO: if final-steps in the result, go tot the self checks node.
    # goto_self_checks_node(result, "Determine_Processing_Steps")
    node = "Determine_Processing_Steps"
    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
        logger.info(f'final steps were detected at the {node} node')
    
        if st.session_state.use_self_checks:
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name=node)
                    ]
                },
                goto="__end__",
            )
        
    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"][-1].content, name="Determine_Processing_Steps")
            ]
        },
        goto="__end__",
    )

Generate_Final_Steps_agent = create_react_agent(
    llm_o3_medium, tools=[], prompt="""Your role is to properly order the steps and present them in the format 
    required by AutoLabs. That is using <final-steps> tags. Make sure that proper chemical names SHOULD be used 
    in chemical addition steps.
    """
)

# ----------------
# Final Steps Node
# ----------------
def final_steps_node(state: State) -> Command[Literal["__end__"]]:
    logger.info('At the final_steps_node')

    with st.sidebar:
        st.markdown("At the final_steps_node.")


    result = Generate_Final_Steps_agent.invoke(state)
    logger.info(f'generated results: {result["messages"][-1].content}')
    # messages = result['messages']
    #------------------------------------------------------
    # if "<final-steps>" in result['messages'][-1].content:

    #     with st.sidebar:
    #         st.markdown('self checks running...')

    #     _, assistant_response = refine_units(messages, llm)
    #     result['messages'].append(assistant_response)
    #------------------------------------------------------

    # goto_self_checks_node(result)


    if "<final-steps>" in result['messages'][-1].content and  '</final-steps>' in result['messages'][-1].content:
    
        if st.session_state.use_self_checks:
            logger.info('final steps detected at the final_steps_node.')
            logger.info('Using self checks. Sending the final steps to self-checks node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name="Generate_Final_Steps")
                    ]
                },
                goto="Self_Checks",
            )
        
        elif st.session_state.use_self_checks_reasoning:
            logger.info('Using reasoning self checks. Sending the final steps to self-checks-reasoning node.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name="Generate_Final_Steps")
                    ]
                },
                goto="Self_Checks_Reasoning",
            )
        
        else:
            # we are only updating the message state using the last message
            logger.info('not using self checks.')
            return Command(
                update={
                    "messages": [
                        AIMessage(content=result["messages"][-1].content, name="Generate_Final_Steps")
                    ]
                },
                goto="__end__",
            )
    





