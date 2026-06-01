from typing import TypedDict, List, Dict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next: str
    user_query: str
    chat_history: str
    agent_context: str
    final_response: str
    execution_trace: Annotated[List[Dict[str, str]], operator.add]
    chat_id: str
    customer_name: str
