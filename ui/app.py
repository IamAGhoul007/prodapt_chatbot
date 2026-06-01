import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st
import time
import requests
import uuid
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from orchestration.graph import build_graph
from orchestration.state import AgentState

st.set_page_config(page_title="Prodapt AI Operations Center", layout="wide")

@st.cache_resource
def get_app():
    return build_graph()

graph_app = get_app()

def check_db_status():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'telecom_ops.db')
    return "Ready" if os.path.exists(db_path) else "Run init_db.py"

def check_vector_status():
    idx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'vector_index')
    return "Built" if os.path.exists(idx_path) else "Will build on first RAG query"

def check_adk_status(port):
    try:
        requests.get(f"http://localhost:{port}/.well-known/agent-card.json", timeout=1)
        return "Running"
    except:
        return "Not running"

# Sidebar
with st.sidebar:
    st.header("System Status")
    st.write(f"**Database:** {check_db_status()}")
    st.write(f"**Vector Index:** {check_vector_status()}")
    
    net_status = check_adk_status(8001)
    bill_status = check_adk_status(8002)
    st.write(f"**Network ADK (8001):** {net_status}")
    st.write(f"**Billing ADK (8002):** {bill_status}")
    
    if net_status == "Not running" or bill_status == "Not running":
        st.warning("Start ADK services: `python adk-services/network_diagnostics/agent.py` and `python adk-services/billing_resolution/agent.py`")
        
    st.header("Framework Map")
    st.markdown("""
    | Capability | Framework |
    |---|---|
    | Policy FAQ | LlamaIndex RAG |
    | Analytics | Semantic SQL |
    | Diagnostics | Google ADK A2A |
    | Orchestration | LangGraph |
    | Final Comms | CrewAI |
    """)

# Main Content
st.title("📡 Prodapt AI Operations Center")
st.caption("Multi-Framework Agentic AI · LangGraph · LlamaIndex · Google ADK · CrewAI")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

# Display history
for msg_idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.success(msg["content"])
            if msg.get("trace"):
                with st.expander("Agent Execution Trace", expanded=False):
                    for idx, step in enumerate(msg["trace"]):
                        st.markdown(f"### Step {idx+1} — {step['worker']}")
                        st.text_area(label=f"trace_{idx}_hist", value=str(step['output']), height=250, disabled=True, key=f"hist_{msg_idx}_{idx}")

if prompt := st.chat_input("Enter customer inquiry... (e.g. 'Customer CUST-10002 was charged twice')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing inquiry through multi-agent system..."):
            try:
                chat_history = ""
                # Get the last 5 successful turns (10 messages) excluding the current one
                recent_msgs = st.session_state.messages[-11:-1] if len(st.session_state.messages) > 1 else []
                if recent_msgs:
                    history_lines = []
                    for m in recent_msgs:
                        role = "Customer" if m["role"] == "user" else "Agent"
                        # Only include successful agent responses or user queries, skip if error
                        if "Error:" not in str(m["content"]):
                            history_lines.append(f"{role}: {m['content']}")
                    chat_history = "\n".join(history_lines)

                initial_state = {
                    "user_query": prompt, 
                    "execution_trace": [], 
                    "agent_context": "", 
                    "messages": [], 
                    "chat_history": chat_history,
                    "chat_id": st.session_state.chat_id
                }
                final_state = graph_app.invoke(initial_state)
                
                final_response = final_state.get('final_response', "Error: No final response generated.")
                trace = final_state.get('execution_trace', [])
                
                st.success(final_response)
                
                with st.expander("Agent Execution Trace", expanded=True):
                    if not trace:
                        st.info("No workers executed.")
                    else:
                        for idx, step in enumerate(trace):
                            st.markdown(f"### Step {idx+1} — {step['worker']}")
                            st.text_area(label=f"trace_{idx}", value=str(step['output']), height=250, disabled=True, key=f"curr_{len(st.session_state.messages)}_{idx}")
                            
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_response, 
                    "trace": trace
                })
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
