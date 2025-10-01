import chromadb
import pandas as pd
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("CLOUD_LLM_API_KEY")

# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-mpnet-base-v2')
# chroma_client = chromadb.PersistentClient(path='./chroma_db')
# collection = chroma_client.get_or_create_collection(
#     name='my_collection',
#     embedding_function=sentence_transformer_ef)

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    api_base="https://ai-incubator-api.pnnl.gov",
)
chroma_client = chromadb.PersistentClient(path="data/steps/oai_chroma_db")
collection = chroma_client.get_or_create_collection(
    name="oai_embeddings",
    # embedding_function=sentence_transformer_ef
    embedding_function=openai_ef,
)


def create_domain_knowledge(objs, steps):

    add = ""
    for i in range(1):

        ex = f"""\n\nEXPERIMENT OBJECTIVE: {objs[i]}
    
    \n\nSTEPS:\n {steps[i]}    
    """

        add += ex

    return add


def get_rag_examples(user_prompt):

    results = collection.query(
        query_texts=[user_prompt], n_results=1, include=["documents", "metadatas"]
    )

    steps = [results["metadatas"][0][i]["steps"] for i in range(1)]
    objs = [results["documents"][0][i] for i in range(1)]

    additional_text = create_domain_knowledge(objs, steps)
    return additional_text


API_KEY = os.environ.get("CLOUD_LLM_API_KEY")
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    api_base="https://ai-incubator-api.pnnl.gov",
    model_name="text-embedding-ada-002",
)

chroma_client = chromadb.PersistentClient(path="./rag/oai_chroma_db")
collection = chroma_client.get_or_create_collection(
    name="oai_embeddings",
    # embedding_function=sentence_transformer_ef
    embedding_function=openai_ef,
)


def processing_steps_rag(user_prompt):

    results = collection.query(
        query_texts=[user_prompt], n_results=3, include=["documents", "metadatas"]
    )

    docs = results["documents"][0]
    md = results["metadatas"][0]
    steps = [i["steps"] for i in md]

    context = [
        f"""
    objective:
    {docs[i]}

    steps:
    {steps[i]}
    """
        for i in range(len(steps))
    ]

    context = "\n".join(context)

    return context
