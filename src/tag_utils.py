import streamlit as st
import numpy as np
from .chem_utils import get_chem_name

def get_chem_state(completer, current_step_text):

    # response = client.chat.completions.create(
    #         model="gpt-4o",
    #         messages=[
    #         {"role":"system", "content": f'Return only the chemical name in this. Do not change it.\n {current_step_text} '
    #         }]
    #         )

    # @gihan - commented
    # messages=[
    #     {"role":"system", "content": f'Return only the chemical name in this. Do not change it.\n {current_step_text} '
    #      }]
    # response = completer.get_chat_completions(messages)
    # chem_name = response.choices[0].message.content


    # @gihan using a new function to get chem_name
    chem_name = get_chem_name(completer, current_step_text)
    
    # response = client.chat.completions.create(
    # model="gpt-4o",
    # messages=[ {"role": "system", "content": f"you are an expert chemist. if {chem_name} is in solid form at room temperature return 1 else 0. just return the number."}
    # ])
    messages=[{"role": "system", "content": f"you are an expert chemist. if {chem_name} is in solid form at room temperature return 1 else 0. just return the number."}]
    response = completer.get_chat_completions(messages)

    solid_liquid = int(response.choices[0].message.content)
    print('solid_liquid: ', solid_liquid)
    if solid_liquid == 1:
        chem_state='solid'
    else:
        chem_state='liquid'
    print('chem_state: ', chem_state)
    return chem_name, chem_state


def SyringePump():
    optional_tags = list(np.array(['Backsolvent', 'LookAhead', 'SourceTracking', \
                                    'DestinationTracking', 'Hover', 'StartVialTimer','WaitVialTimer',\
                                          'Notify'])[[st.session_state.op1, st.session_state.op2,
                                                      st.session_state.op3, st.session_state.op4, \
                                                        st.session_state.op5, st.session_state.op6,\
                                                            st.session_state.op7, st.session_state.op8]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option, 
                                                                      st.session_state.level2]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

def PDT():
    optional_tags = list(np.array(['LookAhead', 'SourceTracking', 'DestinationTracking',\
                                   'ZSample', 'Hover', 'CapAfterDispense', 'NewTip',\
                                    'StartVialTimer', 'WaitVialTimer', 'Notify'])[[st.session_state.op1,st.session_state.op2,\
                                                                                   st.session_state.op3,st.session_state.op4,\
                                                                                   st.session_state.op5,st.session_state.op6,\
                                                                                   st.session_state.op7,st.session_state.op8,\
                                                                                   st.session_state.op9,st.session_state.op10
                                                                                   ]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option, 
                                                                      st.session_state.level2]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

def FourTip():
    optional_tags = list(np.array(['Backsolvent', 'LookAhead', 'SourceTracking',\
                                   'DestinationTracking', 'StartVialTimer', 'WaitVialTimer', 'Notify'])[[st.session_state.op1,st.session_state.op2,\
                                                                                                         st.session_state.op3,st.session_state.op4,\
                                                                                                            st.session_state.op5,st.session_state.op6,
                                                                                                            st.session_state.op7]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None

    
def Powder():
    print('at powder')
    optional_tags = list(np.array(['Plate', 'Notify'])[[st.session_state.op1,st.session_state.op2]])
    st.session_state.tag_options.append({st.session_state.step_text: [st.session_state.level1_option]+optional_tags
                                         })
    st.session_state.tag_counter +=1
    st.session_state.level1_option = None





# response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#         {"role":"system", "content": f'Return only the chemical name in this. Do not change it.\n {current_step_text} '
#         }]
#         )
# chem_name = response.choices[0].message.content

# response = client.chat.completions.create(
# model="gpt-4o",
# messages=[ {"role": "system", "content": f"you are an expert chemist. if {chem_name} is in solid form at room temperature return 1 else 0. just return the number."}
# ])
# solid_liquid = int(response.choices[0].message.content)
# print('solid_liquid: ', solid_liquid)
# if solid_liquid == 1:
#     chem_state='solid'
# else:
#     chem_state='liquid'
# print('chem_state: ', chem_state)