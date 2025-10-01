# from .lschemicals import get_mol_wt, get_mol_density
from .config import Client
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
import os
from typing import Annotated, TypedDict, Literal
import streamlit as st
import logging
logger = logging.getLogger('main_logger')
load_dotenv()

# completer = Client('unfiltered')
# load_dotenv()
logger.info(f'at tools_chem.py - streaming = {st.session_state.streaming}')

from .config import model
# model = AzureChatOpenAI(
#     model='gpt-4o',
#     temperature=0.0,
#     streaming=st.session_state.streaming,
#     max_tokens=None,
#     timeout=None,
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
#     api_version="2024-05-01-preview",
#     azure_endpoint="https://autolabs.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
# )

import pubchempy as pcp
def get_mol_wt(chem_name, completer):
    try:
        results = pcp.get_compounds(chem_name, 'name')
        c = pcp.Compound.from_cid(results[0].cid)
        molw = c.molecular_weight
    except Exception:
        try:
            messages = [{"role": "user", "content": f"return only the molecular weight of {chem_name} in g/mol. do not include units in the returned value."}]
            response = completer.get_chat_completions(messages)
            # response = model.invoke(messages)
            molw = response.choices[0].message.content
            # molw = response.content
            float(molw)
        except Exception:
            molw = 0

    return molw

def get_mol_density(chem_name, completer):
    
    messages = [{"role": "user", "content": f"return only the molecular density of {chem_name} in g/cm3. do not include units in the returned value."}]
    response = completer.get_chat_completions(messages)
    # response = model.invoke(messages)
    mol_density = response.choices[0].message.content
    # mol_density = response.content

    try: 
        float(mol_density)
    except Exception:
        mol_density = '1.'

    return mol_density

def get_chem_state(chem_name, model):


    messages=[SystemMessage(f"you are an expert chemist. if {chem_name} is in solid form at room temperature return 1 else 0. just return the number.")]
    response = model.invoke(messages)

    solid_liquid = int(response.content)
    print('solid_liquid: ', solid_liquid)
    if solid_liquid == 1:
        chem_state='solid'
    else:
        chem_state='liquid'
    print('chem_state: ', chem_state)
    return chem_name, chem_state


@tool
def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


# @tool
# def get_chem_volume(
#     chem_name: str,
#     chem_weight: float):
#     """
#     use this to find the volume of a chemical given its name 
#     """

#     density = float(get_mol_density(chem_name, completer)) # get density # in g/ml

#     volume = chem_weight/density

#     return volume

# @tool
# def find_chemical_amounts_in_a_mixture(
#     total_molarity: Annotated[float, "total molarity of the two chemicals"],
#     molar_ratio: Annotated[float, "molar ratio between two chemicals"],
#     chemicalA_name: Annotated[str, "name of the 1st chemical in the ratio"],
#     chemicalB_name: Annotated[str, "name of the second chemical in the ratio"],
#     solution_volume: Annotated[float, "volume of the solution chemicals are in"],
# ) -> dict:
#     """
#     Calculate how many mili grams or micro litres of each chemical are needed to create
#     a solution with given total molarity and volume. Molar ratio b/w tow chemical are given by molar_ratio.
#     """
#     with st.sidebar:
#         st.markdown('using find_chemical_amounts_in_a_mixture')
        
#     total_molarity = float(total_molarity)
#     molar_ratio = float(molar_ratio)
    
#     # M_A + M_B = total_molarity

#     M_B = total_molarity/(molar_ratio + 1)
#     M_A = M_B*molar_ratio

#     # calculations for chemical A
#     M_A = total_molarity - M_B


#     N_A = M_A * solution_volume
#     MW_A = float(get_mol_wt(chemicalA_name, completer)) # get the molecular weight of A
#     W_A = MW_A * N_A


#     N_B = M_B * solution_volume
#     MW_B = float(get_mol_wt(chemicalB_name, completer)) # get MW
#     W_B = N_B * MW_B

#     # get chem state

#     _, state = get_chem_state(chemicalA_name, completer)

#     if state == 'solid':
        
#         amount_A = W_A

#     elif state == 'liquid':
        
#         D_A = float(get_mol_density(chemicalA_name, completer)) # get density # in g/ml
    
#         V_A = W_A/D_A
#         amount_A = V_A
        
#     # do the same for B

#     _, state = get_chem_state(chemicalB_name, completer)

#     if state == 'solid':
        
#         amount_B = W_B

#     elif state == 'liquid':
        
#         D_B = float(get_mol_density(chemicalB_name, completer)) # get density # in g/ml
    
#         V_B = W_B/D_B
#         amount_B = V_B
    
#     return {
#         chemicalA_name : amount_A,
#         chemicalB_name : amount_B,
#     }

@tool
def find_chemical_amounts_in_a_solution(
    total_molarity: Annotated[float, "total molarity of the two chemicals"],
    molar_ratio: Annotated[float, "molar ratio between two chemicals"],
    chemicalA_name: Annotated[str, "name of the 1st chemical in the ratio"],
    chemicalB_name: Annotated[str, "name of the second chemical in the ratio"],
    solution_volume: Annotated[float, "volume of the solution chemicals are in"],
) -> dict:
    """
    Use this to calculate how many mili grams or micro litres of two chemicals are needed to create
    a solution with given total molarity and volume. IMPRTANT: USE THIS ONLY WHEN YOU CAN CLEARLY FIND THE MOLAR RATIO
    IN THE DESCRIPTION.
    """
        
    total_molarity = float(total_molarity)
    molar_ratio = float(molar_ratio)
    
    # M_A + M_B = total_molarity

    M_B = total_molarity/(molar_ratio + 1)
    M_A = M_B*molar_ratio

    # calculations for chemical A
    M_A = total_molarity - M_B


    N_A = M_A * solution_volume
    MW_A = float(get_mol_wt(chemicalA_name, model)) # get the molecular weight of A
    W_A = MW_A * N_A


    N_B = M_B * solution_volume
    MW_B = float(get_mol_wt(chemicalB_name, model)) # get MW
    W_B = N_B * MW_B

    # get chem state

    _, state = get_chem_state(chemicalA_name, model)

    if state == 'solid':
        
        # amount_A = W_A
        D_A = float(get_mol_density(chemicalA_name, model)) # get density # in g/ml
    
        V_A = W_A/D_A
        amount_A = V_A

    elif state == 'liquid':
        
        D_A = float(get_mol_density(chemicalA_name, model)) # get density # in g/ml
    
        V_A = W_A/D_A
        amount_A = V_A
        
    # do the same for B

    _, state = get_chem_state(chemicalB_name, model)

    if state == 'solid':
        
        # amount_B = W_B
        D_B = float(get_mol_density(chemicalB_name, model)) # get density # in g/ml
        V_B = W_B/D_B
        amount_B = V_B

    elif state == 'liquid':
        
        D_B = float(get_mol_density(chemicalB_name, model)) # get density # in g/ml
    
        V_B = W_B/D_B
        amount_B = V_B
    
    return {
        chemicalA_name : amount_A,
        chemicalB_name : amount_B,
    }


@tool
def get_chem_volume(
    chem_name: str,
    chem_weight: float):
    """
    use this to find the volume of a chemical given its name and its weight in SI units.
    """

    density = float(get_mol_density(chem_name, model)) # get density # in g/ml

    volume = chem_weight/density

    return volume


@tool
def find_the_volume_corresponding_to_moles(
    chem_name: Annotated[str, "name of the chemical"], 
    num_moles: Annotated[float, "number of moles in SI units"]):

    """
    use this to find the volume of a chemical given its name and the number of moles in SI units.
    """
    
    # get the molecular weight of the chemical
    MW = float(get_mol_wt(chem_name, model))
    print(f"MW: {MW}")

    # get the total weight of the chemical
    W = MW*num_moles

    # get molecular density
    D = float(get_mol_density(chem_name, model))
    print(f"D: {D}")
    # volume
    V = W/D

    return V    

def get_chem_state_from_name(chem_name, model):


    messages=[SystemMessage(f"you are an expert chemist. if {chem_name} is in solid form at room temperature return 1 else 0. just return the number.")]
    response = model.invoke(messages)

    solid_liquid = int(response.content)
    print('solid_liquid: ', solid_liquid)
    if solid_liquid == 1:
        chem_state='solid'
    else:
        chem_state='liquid'
    print('chem_state: ', chem_state)
    return chem_name, chem_state


@tool
def find_the_concentration_of_n_percent_solution(
    chem_name: Annotated[str, "name of the chemical"]):

    """
    use this to find the concentration of an n% solution.
    """
    n = float(model.invoke([HumanMessage(f"What is the weight percentage of this chemical. chemical = {chem_name}. return only the percentage.")]).content)
    # get the molecular weight of the chemical

    MW = float(get_mol_wt(chem_name, model))
    
    # get molecular density
    D = float(get_mol_density(chem_name, model))

    # Calculate the mass of chem in 1 L of solution
    mass = 1000 * D

    # mass of n%
    mass_n_percent = n * mass/100

    # Calculate the number of moles
    moles = mass_n_percent/MW

    concentration = moles/1

    return concentration


@tool
def find_the_concentration_of_n_percent_solution(
    chem_name: Annotated[str, "name of the chemical"]):

    """
    use this to find the concentration of an n% solution.
    """
    n = float(model.invoke([HumanMessage(f"What is the weight percentage of this chemical. chemical = {chem_name}. return only the percentag without % symbol.")]).content)
    # get the molecular weight of the chemical

    MW = float(get_mol_wt(chem_name, model))
    
    # get molecular density
    D = float(get_mol_density(chem_name, model))

    # Calculate the mass of chem in 1 L of solution
    mass = 1000 * D

    # mass of n%
    mass_n_percent = n * mass/100

    # Calculate the number of moles
    moles = mass_n_percent/MW

    concentration = moles/1

    return concentration


@tool
def find_stock_solution_volume_corresponding_to_a_modifier(
    stock_sol_concentration: Annotated[str, "concentration of the the stock solution"],
    final_solution_volume: Annotated[str, "volume of the final volume"],
    modifier_concentration: Annotated[str, "concentration of the modifier in the final solution"]
    ):

    """
    use this to find the volume of the stock solution to achieve a specific modifier concentration in the final volume.
    use decimal equivalents of stock_sol_concentration  and modifier_concentration.
    """
    


    modifier_volume = modifier_concentration * final_solution_volume
    stock_vol = (100/stock_sol_concentration)*modifier_volume
    return stock_vol