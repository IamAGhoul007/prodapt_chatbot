import os
from sqlalchemy import create_engine, MetaData
from llama_index.core import SQLDatabase, VectorStoreIndex
from llama_index.core.objects import ObjectIndex, SQLTableSchema
from llama_index.core.query_engine import SQLTableRetrieverQueryEngine
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings

from dotenv import load_dotenv
load_dotenv()

llm = Gemini(model_name="models/gemini-2.5-flash")
embed_model = GeminiEmbedding(model_name="models/gemini-embedding-001")

Settings.llm = llm
Settings.embed_model = embed_model

_sql_query_engine = None

def get_sql_query_engine():
    global _sql_query_engine
    if _sql_query_engine is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'telecom_ops.db')
        engine = create_engine(f"sqlite:///{db_path}")
        metadata = MetaData()
        metadata.reflect(engine)
        
        sql_database = SQLDatabase(engine)
        
        # We need to map the tables with explicit context strings
        context_dict = {
            "network_towers": "Inventory of telecom towers. Contains region, city, technology (LTE, 5G), operational status, capacity, and last maintenance dates.",
            "network_outages": "Historical network outage records. Contains start and end times, severity (CRITICAL, HIGH, MEDIUM, LOW), root cause, affected customers, and the associated tower_id.",
            "tower_performance": "Live telemetry and performance metrics for network towers. Contains average latency (ms), packet loss percentage, throughput (mbps), and signal strength (dbm) for a tower_id at a recorded_at timestamp.",
            "open_incidents": "Active Network Operations Center (NOC) incidents linked to towers. Contains severity, status (OPEN, IN_PROGRESS), description, ETA, and tower_id.",
        }
        
        ALLOWED_TABLES = [
            "network_towers",
            "network_outages",
            "tower_performance",
            "open_incidents"
        ]
        
        table_schema_objs = [
            SQLTableSchema(table_name=t, context_str=context_dict.get(t, "")) for t in ALLOWED_TABLES
        ]
        
        obj_index = ObjectIndex.from_objects(
            table_schema_objs,
            index_cls=VectorStoreIndex,
        )
        
        _sql_query_engine = SQLTableRetrieverQueryEngine(
            sql_database,
            obj_index.as_retriever(similarity_top_k=2),
        )
    return _sql_query_engine

def query_network_analytics(query: str) -> str:
    """
    Answers an analytics question by translating text to SQL against telecom_ops.db.
    """
    blocked_words = [
        "billing",
        "customer",
        "account",
        "credit",
        "charge",
        "cust-"
    ]

    if any(word in query.lower() for word in blocked_words):
        return "Billing data requests must be handled by BillingResolutionADK."

    engine = get_sql_query_engine()
    response = engine.query(query)
    return str(response)

if __name__ == '__main__':
    # Test
    print(query_network_analytics("Which region had the most CRITICAL outages?"))
