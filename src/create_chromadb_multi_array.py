from chromadb.utils import embedding_functions
import chromadb
import os
import pandas as pd
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.environ.get("CLOUD_LLM_API_KEY")
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    api_base="https://ai-incubator-api.pnnl.gov",
    # model_name="gpt-4o",
    # base_url="https://ai-incubator-api.pnnl.gov",
    # model="gpt-4o"
)

# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-mpnet-base-v2')
chroma_client = chromadb.PersistentClient(path="./data/embeddings/chroma_db_mult")
collection = chroma_client.get_or_create_collection(
    name="oai_embeddings_mult", embedding_function=openai_ef
)

data = pd.read_pickle("data/finetune/multi_array.pkl")

qs = [i["question"] for i in data]
ans = [{"steps": i["answer"]} for i in data]
fs = [i["file"] for i in data]

collection.add(documents=qs, metadatas=ans, ids=fs)
