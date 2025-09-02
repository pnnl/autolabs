import os
import openai
from openai import AzureOpenAI
from dotenv import load_dotenv
from langchain.tools import BaseTool
from typing import Union
  

from openai import OpenAI
import json

# client = OpenAI()

# tools = [{
#     "type": "function",
#     "function": {
#         "name": "calculate_chemical_volume",
#         "description": "Calculate the volume of a chemical quantity.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "density": {"type": "number"},
#                 "weight": {"type": "number"}
#             },
#             "required": ["density", "weight"],
#             "additionalProperties": False
#         },
#         "strict": True
#     }
# }]

# def calculate_chemical_volume(density, weight):

#     vol = weight/density
    
#     return float(vol)



load_dotenv()

class Client:
    def __init__(self, clinet_type: str):

        self.clinet_type = clinet_type
        self.get_client()

        if clinet_type =='unfiltered':
            self.get_chat_completions = self.get_chat_completions_gpt_4o
        elif clinet_type =='reasoning':
            self.get_chat_completions = self.get_chat_completions_o3_mini

    def get_client(self):
        if self.clinet_type == 'unfiltered':
            self.client = get_unfiltered_client()
        elif self.clinet_type=="filtered":
            self.client = get_filtered_client()
        elif self.clinet_type=="reasoning":
            self.client = get_resoning_client()

    def get_chat_completions_o3_mini(self, messages):
        response = self.client.chat.completions.create(
            model="o3-mini",
            reasoning_effort="medium",
            messages=messages
            )
        return response
    
    def get_chat_completions_gpt_4o(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            temperature = 0,
            # tools=tools,
            messages=messages
            )
        return response



def get_client(clinet_type):
    if clinet_type == 'unfiltered':
        return get_unfiltered_client()
    elif clinet_type=="filtered":
        return get_filtered_client()
    elif clinet_type=="reasoning":
        return get_resoning_client()

def get_resoning_client():
    client = AzureOpenAI(
        
        api_key=os.getenv("AZURE_OPENAI_API_REASONING_KEY"),  
        api_version="2024-12-01-preview",
        azure_endpoint="https://autolabs-reasoning.openai.azure.com/openai/deployments/o3-mini/chat/completions?api-version=2024-12-01-preview"
    )
    print('Reasoning client')
    return client


def get_unfiltered_client():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version="2024-05-01-preview",
        # azure_endpoint="https://ai-autolabs580778668984.openai.azure.com/"
        azure_endpoint="https://autolabs.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    )
    print('Unifiltered')
    return client


def get_filtered_client():
    API_KEY = os.environ.get("CLOUD_LLM_API_KEY")
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url="https://ai-incubator-api.pnnl.gov"
    )
    print('AI incubator')
    return client
