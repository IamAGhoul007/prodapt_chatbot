import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
# Reconfigure stdout/stderr to utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from orchestration.graph import build_graph
import json
import sys

def test():
    print("Building graph...")
    app = build_graph()
    # Test specific query that gets stuck
    state = {
        "user_query": "My 5G keeps dropping in Austin near tower TX-512. Please diagnose.",
        "execution_trace": [],
        "agent_context": "",
        "messages": []
    }
    print("Invoking graph...")
    result = app.invoke(state)
    print("Final Response:", result.get("final_response"))
    print("Trace:")
    for t in result.get("execution_trace", []):
        print(t)

if __name__ == "__main__":
    test()
