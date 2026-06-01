import os
import sys
import re
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

# Add project root to sys path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from orchestration.state import AgentState
from llamaindex_rag.document_rag import answer_policy_question
from llamaindex_rag.sql_semantic_search import query_network_analytics
from orchestration.adk_remote_client import invoke_network_adk, invoke_billing_adk
from orchestration.crew_nodes import format_customer_response

# Use gemini-2.5-flash with thinking disabled — avoids empty-output error
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
    thinking_budget=0,  # disable thinking tokens to get reliable text output
)

VALID_ROUTES = [
    "policy_rag",
    "network_analytics",
    "network_diagnostics_adk",
    "billing_resolution_adk",
    "customer_comms_crew",
    "FINISH",
]

def security_gate_node(state: AgentState) -> dict:
    query = state.get('user_query', '').lower()
    BLOCKED_PATTERNS = [
        "ignore previous instructions",
        "i am admin",
        "system prompt",
        "show database",
        "dump data",
        "reveal all users",
        "bypass security",
    ]
    
    if any(pattern in query for pattern in BLOCKED_PATTERNS):
        return {
            "final_response": "Access denied. Security policy violation detected.",
            "execution_trace": [{"worker": "SecurityGuard", "output": "Blocked due to prompt injection attempt"}]
        }
    return {}

def supervisor_node(state: AgentState) -> dict:
    query = state.get('user_query', '')
    context = state.get('agent_context', '')
    has_final = bool(state.get('final_response', ''))
    chat_history = state.get('chat_history', '')
    chat_id = state.get('chat_id', 'unknown')
    
    if has_final:
        return {"next": "FINISH"}
    
    trace = state.get('execution_trace', [])
    visited_workers = [t.get('worker') for t in trace if 'worker' in t]
    worker_to_route = {
        "PolicyRAG": "policy_rag",
        "NetworkAnalytics": "network_analytics",
        "NetworkDiagnosticsADK": "network_diagnostics_adk",
        "BillingResolutionADK": "billing_resolution_adk",
        "CustomerCommsCrew": "customer_comms_crew"
    }
    visited_routes = [worker_to_route.get(w, w) for w in visited_workers]

    # Loop Prevention & Clarification Check
    failure_keywords = [
        "need tower id", "need tower", "need region", "please provide",
        "insufficient information", "unable to retrieve", "cannot determine",
        "missing required information", "not enough information", "missing", "unavailable", "unable to answer"
    ]
    if trace:
        last_out = str(trace[-1].get('output', '')).lower()
        if any(k in last_out for k in failure_keywords):
            return {"next": "customer_comms_crew"}

    # Retry Tracking (Max 2 visits per route)
    route_counts = {}
    for r in visited_routes:
        route_counts[r] = route_counts.get(r, 0) + 1
    invalid_routes = [r for r, count in route_counts.items() if count >= 2]

    prompt = f"""You are the Supervisor of a Telecom AI Operations Center.
Session Chat ID: {chat_id}
Chat History:
"{chat_history}"

User Query: "{query}"
Context gathered so far: "{context}"
Final response already generated: {has_final}
Routes already executed: {visited_routes}
Routes that must NOT be selected again (exceeded retries): {invalid_routes}

Choose exactly ONE of the following routes and reply with ONLY that route name, nothing else:
- policy_rag          : for policy, roaming, SLA rules, FAQ
- network_analytics   : for outage trends, latency stats, top-N queries against the DB
- network_diagnostics_adk : for live tower diagnostics, signal drops, open incidents, connectivity, outages, tower status
- billing_resolution_adk  : for billing disputes, duplicate charges, credits
- customer_comms_crew : when you have enough info to write the final customer response
- FINISH              : only after customer_comms_crew has already produced a final response

CRITICAL ROUTING RULES:
1. If the user asks about "tower status", "outages", "diagnostics", "connectivity", or "signal issues", you MUST route to network_diagnostics_adk, NOT network_analytics.
2. Do NOT choose a route that is in the 'Routes that must NOT be selected again' list.
3. If you lack information, route to customer_comms_crew to ask the user.
4. Reply with just the route name."""

    try:
        response = llm.invoke(prompt)
        raw = response.content.strip().lower().replace("-", "_").replace(" ", "_")
        
        # Determine the matched route
        matched_route = None
        for route in VALID_ROUTES:
            if route.lower() in raw:
                matched_route = route
                break
                
        if not matched_route:
            matched_route = "FINISH" if has_final else "customer_comms_crew"
            
        # Prevent premature FINISH
        if matched_route == "FINISH" and not has_final:
            matched_route = "customer_comms_crew"
            
        return {"next": matched_route}
    except Exception as e:
        print(f"[Supervisor ERROR]: {e}")
        return {"next": "FINISH" if has_final else "customer_comms_crew"}

def policy_rag_node(state: AgentState) -> dict:
    query_context = f"Chat History:\n{state.get('chat_history', '')}\n\nLatest Query: {state['user_query']}" if state.get('chat_history') else state['user_query']
    resp = str(answer_policy_question(query_context))
    new_context = state.get('agent_context', '') + f"\n[PolicyRAG]: {resp}"
    return {
        "agent_context": new_context,
        "execution_trace": [{"worker": "PolicyRAG", "output": resp}]
    }

def network_analytics_node(state: AgentState) -> dict:
    query_context = f"Chat History:\n{state.get('chat_history', '')}\n\nLatest Query: {state['user_query']}" if state.get('chat_history') else state['user_query']
    resp = str(query_network_analytics(query_context))
    new_context = state.get('agent_context', '') + f"\n[NetworkAnalytics]: {resp}"
    return {
        "agent_context": new_context,
        "execution_trace": [{"worker": "NetworkAnalytics", "output": resp}]
    }

def network_diagnostics_adk_node(state: AgentState) -> dict:
    query_context = f"Chat History:\n{state.get('chat_history', '')}\n\nLatest Query: {state['user_query']}" if state.get('chat_history') else state['user_query']
    resp = str(invoke_network_adk(query_context))
    new_context = state.get('agent_context', '') + f"\n[NetworkDiagnosticsADK]: {resp}"
    return {
        "agent_context": new_context,
        "execution_trace": [{"worker": "NetworkDiagnosticsADK", "output": resp}]
    }

def billing_resolution_adk_node(state: AgentState) -> dict:
    query_context = f"Chat History:\n{state.get('chat_history', '')}\n\nLatest Query: {state['user_query']}" if state.get('chat_history') else state['user_query']
    resp = str(invoke_billing_adk(query_context))
    new_context = state.get('agent_context', '') + f"\n[BillingResolutionADK]: {resp}"
    return {
        "agent_context": new_context,
        "execution_trace": [{"worker": "BillingResolutionADK", "output": resp}]
    }

def customer_comms_crew_node(state: AgentState) -> dict:
    context = state.get('agent_context', '')
    
    import re
    matches = re.findall(r"CUST-\d+", context)
    
    if len(set(matches)) > 1:
        return {
            "final_response": "Security validation failed. Multiple customer records detected.",
            "execution_trace": [{"worker": "CustomerCommsCrew", "output": "Blocked due to privacy policy"}]
        }

    query_context = f"Chat History:\n{state.get('chat_history', '')}\n\nLatest Query: {state['user_query']}" if state.get('chat_history') else state['user_query']
    
    name_prompt = f"Extract the customer's full name from the following text if they explicitly state their name (e.g. 'I am John', 'My name is Jane'). Return ONLY their name. If no name is provided, return exactly 'None'.\nText: {query_context}"
    extracted_name = llm.invoke(name_prompt).content.strip()
    customer_name = extracted_name if extracted_name.lower() != 'none' else None
    
    resp = str(format_customer_response(query_context, context, customer_name))
    # Mask PII
    resp = re.sub(r"(CUST-)\d+", r"\1****", resp)
    
    return {
        "final_response": resp,
        "execution_trace": [{"worker": "CustomerCommsCrew", "output": resp}],
        "customer_name": customer_name or state.get('customer_name', '')
    }

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("security_gate", security_gate_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("policy_rag", policy_rag_node)
    workflow.add_node("network_analytics", network_analytics_node)
    workflow.add_node("network_diagnostics_adk", network_diagnostics_adk_node)
    workflow.add_node("billing_resolution_adk", billing_resolution_adk_node)
    workflow.add_node("customer_comms_crew", customer_comms_crew_node)
    
    workflow.add_edge(START, "security_gate")
    
    workflow.add_conditional_edges(
        "security_gate",
        lambda x: "FINISH" if x.get("final_response") else "supervisor",
        {
            "supervisor": "supervisor",
            "FINISH": END
        }
    )
    
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "policy_rag": "policy_rag",
            "network_analytics": "network_analytics",
            "network_diagnostics_adk": "network_diagnostics_adk",
            "billing_resolution_adk": "billing_resolution_adk",
            "customer_comms_crew": "customer_comms_crew",
            "FINISH": END
        }
    )
    
    workflow.add_edge("policy_rag", "supervisor")
    workflow.add_edge("network_analytics", "supervisor")
    workflow.add_edge("network_diagnostics_adk", "supervisor")
    workflow.add_edge("billing_resolution_adk", "supervisor")
    workflow.add_edge("customer_comms_crew", "supervisor")
    
    return workflow.compile()
