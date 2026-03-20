import requests
import subprocess
import json
from pathlib import Path

def run_health_check(port: int, install_dir: Path, selected_agents: list[str]) -> list[dict]:
    """
    Runs post-installation verification checks.
    Returns a list of dictionaries with 'name', 'status' (bool), and 'suggestion' (str).
    """
    results = []

    # 1. Check Docker Container
    try:
        res = subprocess.run(["docker", "ps", "--filter", "name=openclaw", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=10)
        if "openclaw" in res.stdout:
            results.append({"name": "Docker Container Running", "status": True, "suggestion": ""})
        else:
            results.append({"name": "Docker Container Running", "status": False, "suggestion": "Run 'docker compose up -d' in the installation directory."})
    except Exception as e:
        results.append({"name": "Docker Container Running", "status": False, "suggestion": f"Docker error: {e}"})

    # 2. Check Dashboard API Health
    try:
        # Assuming the dashboard exposes a simple health endpoint
        url = f"http://localhost:{port}/api/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            results.append({"name": "Dashboard API Responding", "status": True, "suggestion": ""})
        else:
            results.append({"name": "Dashboard API Responding", "status": False, "suggestion": f"API returned status {response.status_code}. Check logs."})
    except requests.exceptions.RequestException:
        results.append({"name": "Dashboard API Responding", "status": False, "suggestion": "Dashboard is not reachable. Ensure the container is running and port is correct."})

    # 3. Check Ollama API
    try:
        url = "http://localhost:11434/api/tags"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            results.append({"name": "Ollama Service Responding", "status": True, "suggestion": ""})
        else:
            results.append({"name": "Ollama Service Responding", "status": False, "suggestion": f"Ollama returned status {response.status_code}. Ensure Ollama is running."})
    except requests.exceptions.RequestException:
        results.append({"name": "Ollama Service Responding", "status": False, "suggestion": "Ollama is not reachable. Start the Ollama service manually."})

    # 4. Check Agent JSON Files
    agents_dir = install_dir / "agents"
    missing_agents = []
    invalid_agents = []
    
    for agent in selected_agents:
        agent_file = agents_dir / f"{agent}.json"
        if not agent_file.exists():
            missing_agents.append(agent)
        else:
            try:
                with open(agent_file, "r") as f:
                    data = json.load(f)
                    if ("agent_name" not in data and "name" not in data) or "system_prompt" not in data:
                        invalid_agents.append(agent)
            except json.JSONDecodeError:
                invalid_agents.append(agent)

    if not missing_agents and not invalid_agents:
        results.append({"name": "Agent Profiles Valid", "status": True, "suggestion": ""})
    else:
        suggestion = ""
        if missing_agents:
            suggestion += f"Missing: {', '.join(missing_agents)}. "
        if invalid_agents:
            suggestion += f"Invalid JSON: {', '.join(invalid_agents)}. "
        suggestion += "Try running the setup wizard again to regenerate profiles."
        results.append({"name": "Agent Profiles Valid", "status": False, "suggestion": suggestion})

    return results
