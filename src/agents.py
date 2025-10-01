import copy
from bs4 import BeautifulSoup
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

common_prompt="\nIf this is not the case, please make any neccessary corrections and provide the <final-steps> again. If no changes are needed, please just repeat the original <final-steps>. Please do not apologize for errors or provide a summary of  the changes."



def correct_vial_dims(chat_history, assistant_response, completer):    
    current_history = copy.deepcopy(chat_history)

    # current_history.append({"role": "assistant", "content": assistant_response})
    current_history.append(assistant_response)

    reminder_query = {"role": "system", "content": f"""Reminder: The dimensions of the array depends on the size of the vials used.
- 8x12 array for 1.2 mL vials
- 6x8 array for 2 mL vials
- 4x6 array for 4 or 8 mL vials
- 2x4 array for 20 mL vials.
Make sure that you are using the correct array size for the required volume. Only the vials corresponding to the correct array should be used. 
                      Also make sure that the vial indexing (A1, A2, B1, etc.) is consistent with the selected array.
{common_prompt}
                      """}
    
    current_history.append(reminder_query)
    messages=[
                *current_history
            ]
    
    response = completer.get_chat_completions(messages)
    assistant_response = AIMessage(response.content)
    
    return reminder_query, assistant_response


def refine_dict(chat_history, assistant_response, completer):    
    current_history = copy.deepcopy(chat_history['messages'])
    # current_history
    reminder_query = SystemMessage(f"""Reminder: The dictionary in each <step> should contain key: value pairs. 
                                        The key should be the vial index and value should be a 0 or a positive number. The dictionary SHOULD NOT contain ambiguous characters like ... .
                                        {common_prompt}"""  )
    current_history.append(reminder_query)

    messages=[ 
        *current_history
    ]
    response = completer.get_chat_completions(messages)
    assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response
    


def refine_units(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append(assistant_response)
    
    reminder_query = SystemMessage(f"""Reminder: The units for solid additions should be in mg and the units for liquid additions should be in ul.
                      {common_prompt}""" )
    chat_history.append(reminder_query)


    messages=[ 
                *chat_history
            ]
    assistant_response = model.invoke(messages)
    # result = chat_history.append(assistant_response)

    return reminder_query, assistant_response

def refine_efficiency(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append(assistant_response)

    reminder_query = SystemMessage(f"""Reminder: Please add each input chemical using as few steps as possible.
                      {common_prompt}"""  )
    chat_history.append(reminder_query)

    messages=[ 
        *chat_history
    ]

    assistant_response = model.invoke(messages)
    return reminder_query, assistant_response


def refine_delays(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append(AIMessage(assistant_response))

    reminder_query = SystemMessage(f"""Reminder: Please remember to add a sufficient delay for any heating, stirring, and vortexing steps.
                      {common_prompt}""")
    chat_history.append(reminder_query)

    messages=[ 
        *chat_history
    ]

    assistant_response = model.invoke(messages)
    # assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response

def refine_plates(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append({"role": "assistant", "content": assistant_response})

    reminder_query = {"role": "system", "content": f"""Reminder: Please remember to include the plate name in each step. If there are multiple plates being used, please make sure to use the format "Plate x", where x is the plate number.
                      {common_prompt}"""  }
    chat_history.append(reminder_query)


    messages=[ *chat_history]
    assistant_response = model.invoke(messages)
    # assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response

def refine_transfer(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append({"role": "assistant", "content": assistant_response})

    reminder_query = {"role": "system", "content": f"""Reminder: In steps that involve Transfer, you must include whether it is Uniform or Discrete. Uniform is when the amount being transfered is the same. Discrete is when the amount being transfered is different. Be sure to also include the units of the transfer in the step description.
                      {common_prompt}"""  }
    chat_history.append(reminder_query)


    messages=[ *chat_history]
    assistant_response = model.invoke(messages)
    # assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response

def refine_additions(chat_history, model):
    reminder_query = {"role": "system", "content": f"""Reminder: In steps that involve chemical additions, each addition must be in its own step. Do not include multiple chemical additions in the same step.
                      {common_prompt}"""  }
    chat_history.append(reminder_query)


    messages=[ *chat_history]
    assistant_response = model.invoke(messages)
    # assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response

def refine_solvents(chat_history, model):    
    # current_history = copy.deepcopy(chat_history)
    # current_history.append(AIMessage(assistant_response))

    reminder_query = SystemMessage(f"""Reminder: Please remember to include the type of solvent that is being used. 
                      {common_prompt}""")
    chat_history.append(reminder_query)

    messages=[*chat_history]
    assistant_response = model.invoke(messages)
    # assistant_response = AIMessage(response.content)
    return reminder_query, assistant_response


def find_vial_array_dim(chat_history, model):
    system_message = """What is the required vial array dimension? 
    Remember:
    •	Vial size should be determined based on the target working volumes of the experiment.  
    •	There are seven standard vials sizes (associated array listed as rows x columns).
    •	1mL (8x12), 1.2mL (8x12), 2mL (6x8), 4mL (4x6), 8mL (4x6), 20mL (2x4), and 125mL (1x2)
    Return just the answer enclosed in <dim> tags.
    """
    tmp_hist = copy.deepcopy(chat_history)
    tmp_hist.append(HumanMessage(system_message))

    messages=[*tmp_hist]
    tmp_response = model.invoke(messages)

    resp = tmp_response.content
    soup = BeautifulSoup(resp)
    dim = soup.find('dim').get_text()
    return dim
