import os
from langchain_openai import ChatOpenAI
import openai
from openai import AzureOpenAI
from dotenv import load_dotenv
from langchain.tools import BaseTool
from typing import Union
from openai import OpenAI
import json
import streamlit as st


load_dotenv()

class Client:
    def __init__(self, clinet_type: str):

        self.clinet_type = clinet_type
        self.get_client()

        if clinet_type =='unfiltered':
            self.get_chat_completions = self.get_chat_completions_gpt_4o
        elif clinet_type =='reasoning':
            self.get_chat_completions = self.get_chat_completions_gpt_4o

    def get_client(self):
        self.client = get_resoning_client()

    
    def get_chat_completions_gpt_4o(self, messages):
        with st.sidebar:
            st.markdown(os.getenv('MODEL'))
        response = self.client.chat.completions.create(
            model=str(os.getenv('MODEL')),
            temperature = 0,
            # tools=tools,
            messages=messages
            )
        return response



def get_client(clinet_type):
    return get_resoning_client()


def get_resoning_client():
    client = OpenAI(
        
        api_key=os.getenv("OPENAI_API_KEY"),  
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    print('Reasoning client')
    return client


model = ChatOpenAI(
    model = os.getenv('MODEL'),
    api_key=os.getenv("OPENAI_API_KEY"),  
    # api_version=os.getenv("OPENAI_API_VERSION"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)