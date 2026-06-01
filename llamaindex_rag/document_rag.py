import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize models for LlamaIndex
llm = Gemini(model_name="models/gemini-2.5-flash")
embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

Settings.llm = llm
Settings.embed_model = embed_model

from llama_index.core import StorageContext, load_index_from_storage

_query_engine = None

def get_policy_query_engine():
    global _query_engine
    if _query_engine is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        persist_dir = os.path.join(base_dir, 'data', 'vector_index')
        documents_dir = os.path.join(base_dir, 'data', 'documents')
        
        if os.path.exists(persist_dir):
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            index = load_index_from_storage(storage_context)
        else:
            documents = SimpleDirectoryReader(documents_dir).load_data()
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=persist_dir)
            
        _query_engine = index.as_query_engine(similarity_top_k=3)
    return _query_engine

def answer_policy_question(query: str) -> str:
    """
    Answers a policy question using RAG over the provided text documents.
    """
    engine = get_policy_query_engine()
    response = engine.query(query)
    return str(response)

if __name__ == '__main__':
    # Test
    print(answer_policy_question("What is the roaming policy for Europe?"))
