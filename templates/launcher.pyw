import os
import sys
import subprocess
import webbrowser
import threading
from pathlib import Path

# Load environment variables manually
env_path = Path(__file__).parent / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key] = val

PORT = env_vars.get("OPENCLAW_PORT", "3000")
DASHBOARD_URL = f"http://localhost:{PORT}"

def start_docker():
    """Starts the docker-compose stack."""
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(Path(__file__).parent))

def stop_docker():
    """Stops the docker-compose stack."""
    subprocess.run(["docker", "compose", "down"], cwd=str(Path(__file__).parent))

def open_dashboard(icon=None, item=None):
    """Opens the OpenHands dashboard."""
    webbrowser.open(DASHBOARD_URL)

def view_logs(icon=None, item=None):
    """Opens the docker logs."""
    if sys.platform == "win32":
        subprocess.Popen(["cmd.exe", "/c", "docker compose logs -f & pause"], cwd=str(Path(__file__).parent))
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "cd {Path(__file__).parent} && docker compose logs -f"'])
    else:
        subprocess.Popen(["x-terminal-emulator", "-e", "docker compose logs -f"], cwd=str(Path(__file__).parent))

def stop_app(icon=None, item=None):
    """Stops the docker containers."""
    threading.Thread(target=stop_docker).start()

def quit_app(icon=None, item=None):
    """Stops containers and exits."""
    stop_docker()
    sys.exit(0)

def main():
    start_docker()
    webbrowser.open(DASHBOARD_URL)

if __name__ == "__main__":
    main()
