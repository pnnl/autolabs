from src.inits import init
init()
import os
from dotenv import load_dotenv
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.prompts import system_prompt
from st_callable_util import get_streamlit_cb  # Utility function to get a Streamlit callback handler with context
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
from src.create_lslibrary import get_exp_steps
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

if 'settings_info' in st.session_state:    
    with st.sidebar:
        st.info(f'{st.session_state.settings_info}')


evaluator_name = evaluator.name
completer = Client('unfiltered')
load_dotenv()

st.session_state.streaming = False
st.session_state.timeout=None

def create_logger(results_folder):
        
    log_path = f'{results_folder}/main.log'
    # Set up the logger
    logger = logging.getLogger('main_logger')
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    # Create file handler with the user-specified path
    handler = logging.FileHandler(log_path, mode='w')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

model = AzureChatOpenAI(
    model='gpt-4o',
    temperature=0.0,
    streaming=st.session_state.streaming,
    max_tokens=None,
    timeout=None,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


st.title("AutoLabs")



def save_tmp_chat_history():

    results_dir = f'non-expert-evals/{st.session_state_exp_number_text}'
    with open(f'{st.session_state.eval_results_dir}/chat_history.pkl', 'wb') as f:
        pickle.dump(st.session_state.chat_history, f)

    with open(f'{st.session_state.eval_results_dir}/steps.pkl', 'wb') as f:
        pickle.dump(st.session_state.tmp_steps , f)

    elapsed_time = time.time() - st.session_state.start_time
    token_usage_time = {"Total_Tokens_Used": st.session_state.callback_handler.total_tokens,
            "Prompt_Tokens": st.session_state.callback_handler.prompt_tokens,
            "Completion_Tokens": st.session_state.callback_handler.completion_tokens,
            "Successful_Requests": st.session_state.callback_handler.successful_requests,
            "Total_Cost": st.session_state.callback_handler.total_cost,
            "elapsed_time": elapsed_time
                    
        }

    with open(f'{st.session_state.eval_results_dir}/token_usage_and_time.pkl', 'wb') as f:
        pickle.dump(token_usage_time, f)



with st.sidebar:
    _ = st.button('Save Chat And Steps', on_click=save_tmp_chat_history)

display_chat_history()


def init_graph():
    from graph import Graph, SingleGraph
    st.session_state.callback_handler = OpenAICallbackHandler()

    if st.session_state.grpah_type_ma:
        _graph = Graph(use_self_checks=st.session_state.gpt_4o_self_checks, 
                    use_self_checks_reasoning=st.session_state.reasoning_self_checks, 
                    use_tools=st.session_state.use_tools_form_op,
                    )
        _graph.build_graph()
        _graph.compile_graph()
    else:
        _graph = SingleGraph(use_self_checks=st.session_state.gpt_4o_self_checks, 
                    use_self_checks_reasoning=st.session_state.reasoning_self_checks, 
                    use_tools=st.session_state.use_tools_form_op,
                    )
        _graph.build_graph()
        _graph.compile_graph()


    settings_folder =  'MA' if st.session_state.grpah_type_ma else 'SA'
    if st.session_state.use_tools_form_op == True:
        settings_folder += '-TU'
    if st.session_state.reasoning_self_checks == True:
        settings_folder += '-SCR'
    elif st.session_state.gpt_4o_self_checks == True:
        settings_folder += '-SCNR'

    
    st.session_state.settings_info = f'self-checks: {st.session_state.gpt_4o_self_checks}, reasoning self-checks: {st.session_state.reasoning_self_checks}, use_tools: {st.session_state.use_tools_form_op}'

    st.session_state_exp_number_text = st.session_state.exp_number
    queries = pd.read_pickle('evals/six_user_queries/original/queries.pkl')

    if st.session_state.exp_number is not None:
        query = queries[f'exp{st.session_state.exp_number[-1]}']    

    st.session_state.eval_results_dir=f'non-expert-evals/{evaluator_name}/{settings_folder}/{st.session_state_exp_number_text}'
    os.makedirs(st.session_state.eval_results_dir, exist_ok=True)
    create_logger(st.session_state.eval_results_dir)
    st.session_state.start_time = time.time()

    with st.sidebar:
        st.code(query, language=None, wrap_lines=True)

if st.session_state.iteration_count == 0:

    with st.chat_message("system"):
        st.markdown("Welcome to AutoLabs. Please type the description of your experiment in the box on the left or click on the microphone icon and describe it verbaly.")

    st.session_state.chat_history.append(SystemMessage(system_prompt))
    st.session_state["query_experiment"] = True
    st.session_state.iteration_count +=1

    with st.chat_message("system"):
        st.markdown("Please select the relevant options:")
    
        with st.form(key='graph_options_form'):
            sa_ma = st.toggle("use Multi Agent", value=True, key='grpah_type_ma')
            gpt_4o_self_checks = st.toggle("use gpt-4o self-checks", value=False, key='gpt_4o_self_checks')
            reasoning_self_checks = st.toggle("use reasoning self-checks", value=False, key='reasoning_self_checks')
            use_tools = st.toggle("use tools", value=True, key='use_tools_form_op')

            exp_option = st.selectbox(
                "Select the experiment number.",
                ("Exp1", "Exp2", "Exp3", "Exp4", "Exp5"),
                index=None,
                placeholder="Select experiment",
                key='exp_number'
            )
                        
            submit_graph_form = st.form_submit_button(label='Submit', on_click=init_graph)





if st.session_state["query_experiment"]==True:
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
                
            if len(user_prompt)> 150:
                st.session_state.chat_history.append(SystemMessage("Rewriting the user query improving it's clarity."))
                resp = model.invoke([SystemMessage(f"""Review the user's query and identify any ambiguities or missing details. Rewrite the query for maximum clarity and completeness, ensuring the original intent is preserved.
                                                
                                            user query: {user_prompt}
                                            """)])
                st.session_state.chat_history.append(SystemMessage(f"""Use this rewritten version of the user query to determine experiment steps.
                                                                
                                                                {resp.content}
                                                                """))

        with st.chat_message("assistant"):

            st_callback = get_streamlit_cb(st.container())
            callback=[st_callback]


            response = invoke_our_graph(st.session_state.chat_history, callback)

            assistant_response=response["messages"][-1].content


            if assistant_response and '<final-steps>' in assistant_response and  '</final-steps>' in assistant_response:

                st.session_state.current_steps_text =  assistant_response        
                st.session_state.current_steps = pd.DataFrame(get_exp_steps(assistant_response))
                st.session_state.tmp_steps = get_exp_steps(assistant_response)
                with st.sidebar:
                    st.info(f'final steps: {type(st.session_state.current_steps)}')
              
            if assistant_response:    
                st.session_state.chat_history.append(AIMessage(assistant_response))  
                st.markdown(assistant_response)


display_table()                

if st.session_state.current_steps is not None:
    st.session_state.use_current_steps = st.button("Use Current Steps", on_click=switch_off_querying)


if 'level1_option' not in st.session_state:
    st.session_state.level1_option = None

for op in range(1,9):
    if not f'op{op}' in st.session_state:
        st.session_state[f'op{op}'] = False

def save_options():
    st.session_state.tag_options.append({st.session_state.step_text: st.session_state.step_options
                                         })
def level1():
    st.session_state.level1_option = st.session_state.level1

def SyringePump():
    optional_tags = list(np.array(['Backsolvent', 'LookAhead', 'SourceTracking', \
                                    'DestinationTracking', 'Hover', 'StartVialTimer','WaitVialTimer',\
                                          'Notify'])[[st.session_state.op1, st.session_state.op2,
                                                      st.session_state.op3, st.session_state.op4, \
                                                        st.session_state.op5, st.session_state.op6,\
                                                            st.session_state.op7, st.session_state.op8]])

    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option] + 
                                                                      [st.session_state.level2] + optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

def PDT():
    optional_tags = list(np.array(['LookAhead', 'CapAfterDispense', 'NewTip',\
                                    'StartVialTimer', 'WaitVialTimer', 'Notify'])[[st.session_state.op1,st.session_state.op2,\
                                                                                   st.session_state.op3,st.session_state.op4,\
                                                                                   st.session_state.op5,st.session_state.op6
                                                                                   ]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option, 
                                                                      st.session_state.level2]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

def FourTip():
    optional_tags = list(np.array(['Backsolvent', 'LookAhead', 'StartVialTimer', 'WaitVialTimer', 'Notify'])[[st.session_state.op1,st.session_state.op2,\
                                                                                                         st.session_state.op3,st.session_state.op4,\
                                                                                                            st.session_state.op5,st.session_state.op6,
                                                                                                            st.session_state.op7]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

    
def Powder():
    optional_tags = list(np.array(['Plate', 'Notify'])[[st.session_state.op1,st.session_state.op2]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

def MoveVial():
    optional_tags = list(np.array(['StartVialTimer', 'WaitVialTimer', 'Notify' ])[[st.session_state.op1,st.session_state.op2,st.session_state.op3]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

from src.tag_utils import SyringePump, PDT, FourTip, Powder
from src.tag_utils import get_chem_state

# if st.session_state["query_experiment"] == False:
if st.session_state["work_on_optional_tags"] == True:

    if st.session_state.tag_counter <  len(st.session_state.steps):
        
        i = st.session_state.tag_counter
        st.session_state.step_text = st.session_state.steps[i].get_text() # selected step
        
        current_step_text = st.session_state.step_text
        current_step_text_loc = current_step_text.find('{')  
        current_step_text = current_step_text[:current_step_text_loc]

        with st.chat_message("system"):
            message = f"Please make corrections to the suggested tags for the {current_step_text} step?"
            st.markdown(message)
            
        if st.session_state.tag_counter == 0:
            message_init = f'{tags_prompt}'
            st.session_state.chat_history.append(SystemMessage(message_init))


        if 'add' in current_step_text.lower() and st.session_state.level1_option is None:
        
            chem_name, _chem_state = get_chem_state(completer, current_step_text)

            if '(mg)' in current_step_text.lower():
                chem_state = 'solid'
            elif '(ul)' in current_step_text.lower():
                chem_state = 'liquid'
            else: 
                chem_state = _chem_state

            print('chem_state: ', chem_state)
                
            if chem_state == 'solid':
                default = 'Powder'
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

                messages=[*st.session_state.chat_history,
                        SystemMessage(option_prompt)
                        ]
                response = model.invoke(messages)
                assistant_response = response.content
                selected_tags = []
                for tag in ['SyringePump', 'PDT', '4Tip']:
                    if tag in assistant_response:
                        selected_tags.append(tag)

                if len(selected_tags) == 0:
                    default='SyringePump'
                else:
                    default = selected_tags[0]
                    
            all_level1_options = ['Powder','SyringePump', 'PDT', '4Tip']
            with st.form(key='level1_form'):
                options = st.selectbox(
                        'Dispensing Tags',
                        [default] + [i for i in all_level1_options if i != default],
                        key='level1'
                            )
                l1 = st.form_submit_button(label='Select Main Dispensing Tag', on_click=level1)


        elif 'add' in current_step_text.lower() and st.session_state.level1_option is not None:
                if st.session_state.level1_option == 'SyringePump':
                    with st.form(key='level2_form'):
                            
                        options = st.selectbox(
                            'Dispensing Tags',
                            ['SyringePump'],
                            key='level1',
                            disabled=True
                            )

                            
                        second_level_tags = st.selectbox(
                            '',
                            ['ExtSingleTip'],
                            key='level2'
                            )
                        
                        prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: SyringePump\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['Backsolvent', 'LookAhead', 'SourceTracking', 'DestinationTracking',
                        'Hover', 'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                        """
                        
                        messages=[
                            *st.session_state.chat_history,
                            SystemMessage(prompt)]
                        response = model.invoke(messages)

                        try:
                            options = ast.literal_eval(response.content)
                        except:
                            options = []
                            for opt in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify"]:
                                if opt in response.content:
                                    options.append(opt)
                        
                        print('===options===: ', options)

                        op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify"] }

                        op1 = st.checkbox("Backsolvent", key='op1', value=op_dict["Backsolvent"])
                        op2 = st.checkbox("LookAhead", key='op2', value=op_dict["LookAhead"])
                        op3 = st.checkbox("SourceTracking", key='op3', value=op_dict["SourceTracking"])
                        op4 = st.checkbox("DestinationTracking", key='op4', value=op_dict["DestinationTracking"])
                        op5 = st.checkbox("Hover", key='op5', value=op_dict["Hover"])
                        op6 = st.checkbox("StartVialTimer", key='op6', value=op_dict["StartVialTimer"])
                        op7 = st.checkbox("WaitVialTimer", key='op7', value=op_dict["WaitVialTimer"])
                        op8 = st.checkbox("Notify", key='op8', value=op_dict["Notify"])
                        l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=SyringePump)

                elif st.session_state.level1_option == 'PDT':
                    with st.form(key='level2_form'):
                            
                        options = st.selectbox(
                            'Dispensing Tags',
                            ['PDT'],
                            key='level1',
                            disabled=True
                            )

                        
                        prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: PDT\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['LookAhead', 'SourceTracking', 'DestinationTracking',
                        'Hover', 'StartVialTimer', 'WaitVialTimer','Notify','ZSample','CapAfterDispense','NewTip'] and the available PDT size tags.
                        """

                        messages=[
                            *st.session_state.chat_history,
                            SystemMessage(prompt)
                        ]
                        response = model.invoke(messages)
                        try:
                            options = ast.literal_eval(response.content)
                        except:
                            options = []
                            for opt in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify","ZSample","CapAfterDispense","NewTip"] + ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip']:
                                if opt in response.content:
                                    options.append(opt)
                        
                        print('===options===: ', options)

                        size_tag = [t for t in options if t in ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip']]
                        if len(size_tag) == 0:
                            size_tag = '10mLTip'
                        else:
                            size_tag = size_tag[0]
                            
                        op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify","ZSample","CapAfterDispense","NewTip"] }
                        
                            
                        second_level_tags = st.selectbox(
                            '',
                            [size_tag] + [t for t in ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip'] if t != size_tag],
                            key='level2'
                            )
                        
                        op1 = st.checkbox("LookAhead", key='op1', value=op_dict["LookAhead"])
                        op2 = st.checkbox("SourceTracking", key='op2', value=op_dict["SourceTracking"])
                        op3 = st.checkbox("DestinationTracking", key='op3', value=op_dict["DestinationTracking"])
                        op4 = st.checkbox("ZSample", key='op4', value=op_dict["ZSample"])
                        op5 = st.checkbox("Hover", key='op5', value=op_dict["Hover"])
                        op6 = st.checkbox("CapAfterDispense", key='op6', value=op_dict["CapAfterDispense"])
                        op7 = st.checkbox("NewTip", key='op7', value=op_dict["NewTip"])
                        op8 = st.checkbox("StartVialTimer", key='op8', value=op_dict["StartVialTimer"])
                        op9 = st.checkbox("WaitVialTimer", key='op9', value=op_dict["WaitVialTimer"])
                        op10 = st.checkbox("Notify", key='op10', value=op_dict["Notify"])

                        l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=PDT)
    
                elif st.session_state.level1_option == '4Tip':
                    with st.form(key='level2_form'):
                        # second_level_tags = st.selectbox(
                        #     '',
                        #     [],
                        #     key='level2'
                        #     )
                        
                        options = st.selectbox(
                            'Dispensing Tags',
                            ['4Tip'],
                            key='level1',
                            disabled=True
                            )

                        prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: 4Tip\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['Backsolvent', 'LookAhead', 'SourceTracking', 'DestinationTracking',
                        'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                        """

                        messages=[
                            *st.session_state.chat_history,
                        SystemMessage(prompt)]
                        response = model.invoke(messages)
                        
                        try:
                            options = ast.literal_eval(response.content)
                        except:
                            options = []
                            for opt in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify"]:
                                if opt in response.content:
                                    options.append(opt)
                        
                        print('===options===: ', options)

                        op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                    "StartVialTimer", "WaitVialTimer", "Notify"] }
                        
                        op1 = st.checkbox("Backsolvent", key='op1', value=op_dict["Backsolvent"])
                        op2 = st.checkbox("LookAhead", key='op2', value=op_dict["LookAhead"])
                        op3 = st.checkbox("SourceTracking", key='op3', value=op_dict["SourceTracking"])
                        op4 = st.checkbox("DestinationTracking", key='op4', value=op_dict["DestinationTracking"])
                        op5 = st.checkbox("StartVialTimer", key='op5', value=op_dict["StartVialTimer"])
                        op6 = st.checkbox("WaitVialTimer", key='op6', value=op_dict["WaitVialTimer"])
                        op7 = st.checkbox("Notify", key='op7', value=op_dict["Notify"])
                        l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=FourTip)

                elif st.session_state.level1_option == 'Powder':
                    with st.form(key='level2_form'):
                        
                        options = st.selectbox(
                            'Dispensing Tags',
                            ['Powder'],
                            key='level1',
                            disabled=True
                            )
                        
                        prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: Powder\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['Plate','Notify'] using the above context and rules.
                        """
                        print('-----------------------------------------------------------------')

                        messages=[
                            *st.session_state.chat_history,
                        SystemMessage(prompt)
                        ]
                        response = model.invoke(messages)
                        try:
                            options = ast.literal_eval(response.content)
                        except:
                            options = []
                            for opt in ["Plate","Notify"]:
                                if opt in response.content:
                                    options.append(opt)
                        
                        print('===options===: ', options)

                        op_dict = {k:True if k in options else False for k in ["Plate","Notify"] }
                        op1 = st.checkbox("Plate", key='op1', value=op_dict["Plate"])
                        op2 = st.checkbox("Notify", key='op2', value=op_dict["Notify"])
                        l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=Powder)           
            
        elif 'set' in current_step_text.lower():
            with st.form(key='tags'):
            
                options = st.multiselect(
                            '',
                            tags_values,
                            ['Processing'],
                            key='step_options'
                                )
                submit_button_tags = st.form_submit_button(label='submit tags', on_click=save_options)
            st.session_state.tag_counter +=1
        elif 'transfer' in current_step_text.lower() and st.session_state.level1_option is None:

            if '(mg)' in current_step_text.lower():
                chem_state = 'solid'
            elif '(ul)' in current_step_text.lower():
                chem_state = 'liquid'
            else: 
                chem_state = 'liquid'
                
            if chem_state == 'solid':
                default = 'MoveVial'
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

                messages=[*st.session_state.chat_history,
                        SystemMessage(option_prompt)
                        ]
                response = model.invoke(messages)
                assistant_response = response.content
                selected_tags = []
                # check if the LLMs response is in the allowed options
                for tag in ['SyringePump', 'PDT', '4Tip', 'MoveVial', 'Powder']:
                    if tag in assistant_response:
                        selected_tags.append(tag)
                # if LLM does not respond with allowed responses, choose a default
                if len(selected_tags) == 0:
                    default='SyringePump'
                else:
                    default = selected_tags[0]
                    
            all_level1_options = ['SyringePump', 'PDT', '4Tip', 'MoveVial', "Powder"]
            with st.form(key='level1_form'):
                options = st.selectbox(
                        'Dispensing Tags',
                        [default] + [i for i in all_level1_options if i != default],
                        key='level1'
                            )
                l1 = st.form_submit_button(label='Select Main Dispensing Tag', on_click=level1)
        elif 'transfer' in current_step_text.lower() and st.session_state.level1_option is not None:
            if st.session_state.level1_option == 'SyringePump':
                with st.form(key='level2_form'):
                        
                    options = st.selectbox(
                        'Dispensing Tags',
                        ['SyringePump'],
                        key='level1',
                        disabled=True
                        )

                        
                    second_level_tags = st.selectbox(
                        '',
                        ['ExtSingleTip'],
                        key='level2'
                        )
                    
                    prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                    experiment step: {current_step_text}\n
                    high-level dispensing tag: SyringePump\n
                    context: {additions_prompt_level2}\n
                    return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                    the tags should be selected from the options ['Backsolvent', 'LookAhead', 'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                    """
                    
                    messages=[
                        *st.session_state.chat_history,
                    SystemMessage(prompt)]
                    response = model.invoke(messages)

                    try:
                        options = ast.literal_eval(response.content)
                    except:
                        options = []
                        for opt in ["Backsolvent","LookAhead",
                                                "StartVialTimer", "WaitVialTimer", "Notify"]:
                            if opt in response.content:
                                options.append(opt)
                    
                    print('===options===: ', options)

                    op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead",
                                                "StartVialTimer", "WaitVialTimer", "Notify"] }

                    op1 = st.checkbox("Backsolvent", key='op1', value=op_dict["Backsolvent"])
                    op2 = st.checkbox("LookAhead", key='op2', value=op_dict["LookAhead"])
                    op6 = st.checkbox("StartVialTimer", key='op6', value=op_dict["StartVialTimer"])
                    op7 = st.checkbox("WaitVialTimer", key='op7', value=op_dict["WaitVialTimer"])
                    op8 = st.checkbox("Notify", key='op8', value=op_dict["Notify"])
                    l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=SyringePump)
            elif st.session_state.level1_option == 'PDT':
                    with st.form(key='level2_form'):
                            
                        options = st.selectbox(
                            'Dispensing Tags',
                            ['PDT'],
                            key='level1',
                            disabled=True
                            )

                        
                        prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                        experiment step: {current_step_text}\n
                        high-level dispensing tag: PDT\n
                        context: {additions_prompt_level2}\n
                        return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                        the tags should be selected from the options ['LookAhead', 'StartVialTimer', 'WaitVialTimer','Notify', 'CapAfterDispense','NewTip'] and the available PDT size tags.
                        """

                        messages=[
                            *st.session_state.chat_history,
                        SystemMessage(prompt)]
                        response = model.invoke(messages)
                        try:
                            options = ast.literal_eval(response.content)
                        except:
                            options = []
                            for opt in ["Backsolvent","LookAhead",
                                                    "StartVialTimer", "WaitVialTimer", "Notify","ZSample","CapAfterDispense","NewTip"] + ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip']:
                                if opt in response.content:
                                    options.append(opt)
                        
                        print('===options===: ', options)

                        size_tag = [t for t in options if t in ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip']]
                        if len(size_tag) == 0:
                            size_tag = '10mLTip'
                        else:
                            size_tag = size_tag[0]
                            
                        op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead",
                                                    "StartVialTimer", "WaitVialTimer", "Notify","ZSample","CapAfterDispense","NewTip"] }
                        
                            
                        second_level_tags = st.selectbox(
                            '',
                            [size_tag] + [t for t in ['10mLTip', '1000uLTip', '250uLTip', '100uLTip', '50uLTip', '25uLTip', '10uLTip'] if t != size_tag],
                            key='level2'
                            )
                        
                        op1 = st.checkbox("LookAhead", key='op1', value=op_dict["LookAhead"])
                        op2 = st.checkbox("CapAfterDispense", key='op2', value=op_dict["CapAfterDispense"])
                        op3 = st.checkbox("NewTip", key='op3', value=op_dict["NewTip"])
                        op4 = st.checkbox("StartVialTimer", key='op4', value=op_dict["StartVialTimer"])
                        op5 = st.checkbox("WaitVialTimer", key='op5', value=op_dict["WaitVialTimer"])
                        op6 = st.checkbox("Notify", key='op6', value=op_dict["Notify"])

                        l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=PDT)
    
            elif st.session_state.level1_option == '4Tip':
                with st.form(key='level2_form'):
                    
                    options = st.selectbox(
                        'Dispensing Tags',
                        ['4Tip'],
                        key='level1',
                        disabled=True
                        )

                    prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                    experiment step: {current_step_text}\n
                    high-level dispensing tag: 4Tip\n
                    context: {additions_prompt_level2}\n
                    return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                    the tags should be selected from the options ['Backsolvent', 'LookAhead',
                    'StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                    """

                    messages=[
                        *st.session_state.chat_history,
                    SystemMessage(prompt)]
                    response = model.invoke(messages)
                    
                    try:
                        options = ast.literal_eval(response.content)
                    except:
                        options = []
                        for opt in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                "StartVialTimer", "WaitVialTimer", "Notify"]:
                            if opt in response.content:
                                options.append(opt)
                    
                    print('===options===: ', options)

                    op_dict = {k:True if k in options else False for k in ["Backsolvent","LookAhead","SourceTracking", "DestinationTracking", "Hover",
                                                "StartVialTimer", "WaitVialTimer", "Notify"] }
                    
                    op1 = st.checkbox("Backsolvent", key='op1', value=op_dict["Backsolvent"])
                    op2 = st.checkbox("LookAhead", key='op2', value=op_dict["LookAhead"])
                    op5 = st.checkbox("StartVialTimer", key='op5', value=op_dict["StartVialTimer"])
                    op6 = st.checkbox("WaitVialTimer", key='op6', value=op_dict["WaitVialTimer"])
                    op7 = st.checkbox("Notify", key='op7', value=op_dict["Notify"])
                    l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=FourTip)
            elif st.session_state.level1_option == 'MoveVial':
                with st.form(key='level2_form'):
                    
                    options = st.selectbox(
                        'Dispensing Tags',
                        ['MoveVial'],
                        key='level1',
                        disabled=True
                        )

                    prompt=f"""You have to find the optional tags for the experiment step based on the following context.\n
                    experiment step: {current_step_text}\n
                    high-level dispensing tag: 4Tip\n
                    context: {additions_prompt_level2}\n
                    return all the applicable tags in commma seperated list that can be converted using ast.literal_eval.
                    the tags should be selected from the options ['StartVialTimer', 'WaitVialTimer','Notify'] using the above context and rules.
                    """

                    messages=[
                        *st.session_state.chat_history,
                        SystemMessage(prompt)]
                    response = model.invoke(messages)
                    
                    try:
                        options = ast.literal_eval(response.content)
                    except:
                        options = []
                        for opt in ["StartVialTimer", "WaitVialTimer", "Notify"]:
                            if opt in response.content:
                                options.append(opt)
                    
                    print('===options===: ', options)

                    op_dict = {k:True if k in options else False for k in ["StartVialTimer", "WaitVialTimer", "Notify"] }
                    
                    op1 = st.checkbox("StartVialTimer", key='op1', value=op_dict["StartVialTimer"])
                    op2 = st.checkbox("WaitVialTimer", key='op2', value=op_dict["WaitVialTimer"])
                    op3 = st.checkbox("Notify", key='op3', value=op_dict["Notify"])
                    l2 = st.form_submit_button(label='Select Optional Dispensing Tags', on_click=MoveVial)
        else:
            with st.form(key='tags'):
            
                options = st.multiselect(
                            '',
                            tags_values,
                            ['Processing'],
                            key='step_options'
                                )
                submit_button_tags = st.form_submit_button(label='submit tags', on_click=save_options)
            st.session_state.tag_counter +=1
    

    if st.session_state.tag_counter == len(st.session_state.steps):
        with open('tag_options.pkl', 'wb') as f:
            pickle.dump(st.session_state.tag_options, f)
        path2 = os.path.join(st.session_state.exp_dir, 'tag_options.pkl')
        with open(path2, 'wb') as f:
            pickle.dump(st.session_state.tag_options, f)

        st.session_state['tags_finalized'] = True
        st.session_state["query_experiment"] = False


       


with st.sidebar:
    st.markdown('tag counter:' + str(st.session_state.tag_counter))
    def create_lsr_file():
        file_content = create_xml('current_steps.pkl', 'tag_options.pkl', completer)
        with open('exp.xml', 'w') as file:        
            file.write(file_content)
            file.write('\n')

        path2 = os.path.join(st.session_state.exp_dir, 'exp.xml')
        with open(path2, 'w') as file:        
            file.write(file_content)
            file.write('\n')

        with open('exp.lsr', 'w') as file:        
            file.write(file_content)
            file.write('\n')
            
        path2 = os.path.join(st.session_state.exp_dir, 'exp.lsr')
        with open(path2, 'w') as file:        
            file.write(file_content)
            file.write('\n')

          
    creta_lsr_fle_button = st.button("Create LSR", on_click=create_lsr_file)
    if creta_lsr_fle_button:
        # os.system(f'cp exp.xml {st.session_state.exp_dir}/')
        # os.system(f'cp exp.lsr {st.session_state.exp_dir}/')
        # subprocess.call(f'copy exp.xml {st.session_state.exp_dir}/', shell=True)
        # subprocess.call(f'copy exp.lsr {st.session_state.exp_dir}/', shell=True)

        path2 = os.path.join(st.session_state.exp_dir, 'chat_history.pkl')
        with open(path2, 'wb') as f:
            pickle.dump(st.session_state.chat_history, f)
        st.markdown('LSR file created. File names: exp.xml, exp.lsr')

with st.sidebar:
    if os.path.exists('exp.lsr'):        
        with open('exp.lsr', 'rb') as file:
            xml_data = file.read()

        st.download_button(
            label="Download LSR File",
            data=xml_data,
            file_name="downloaded_LSR.lsr",
            mime="application/xml"
        )

def zip_directory(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
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
    zip_directory('non-expert-evals', 'non_expert_evals.zip')

    with open("non_expert_evals.zip", "rb") as fp:
        st.download_button(
            label="Download Evaluations",
            data=fp,
            file_name="non_expert_evals.zip",
            mime="application/zip"
        )
        
