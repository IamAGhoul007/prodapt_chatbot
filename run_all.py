import subprocess
import time
import sys
import os
import httpx

# Force UTF-8 output so CrewAI emoji logs don't crash on Windows cp1252
os.environ["PYTHONIOENCODING"] = "utf-8"

def wait_for_service(url: str, name: str, timeout: int = 30):
    """Poll until an ADK service is reachable."""
    print(f"  Waiting for {name} at {url}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url + "/.well-known/agent-card.json", timeout=2.0)
            if r.status_code < 500:
                print(f"  [OK] {name} is up!")
                return True
        except Exception:
            pass
        time.sleep(1)
    print(f"  [WARN] {name} did NOT respond within {timeout}s -- continuing anyway.")
    return False

def start_services():
    print("=" * 50)
    print("Starting Network ADK Service on port 8001...")
    network_process = subprocess.Popen(
        [sys.executable, "adk-services/network_diagnostics/agent.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    print("Starting Billing ADK Service on port 8002...")
    billing_process = subprocess.Popen(
        [sys.executable, "adk-services/billing_resolution/agent.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    # Wait for services to come up
    wait_for_service("http://localhost:8001", "Network Diagnostics ADK")
    wait_for_service("http://localhost:8002", "Billing Resolution ADK")

    print("Starting Streamlit UI on port 8501...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    print("=" * 50)
    print("All services started!")
    print("  [1] Network Diagnostics ADK -> http://localhost:8001")
    print("  [2] Billing Resolution ADK  -> http://localhost:8002")
    print("  [3] Streamlit UI            -> http://localhost:8501")
    print("=" * 50)
    print("Press Ctrl+C to stop all services.")

    try:
        network_process.wait()
        billing_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        network_process.terminate()
        billing_process.terminate()
        streamlit_process.terminate()

if __name__ == "__main__":
    start_services()
