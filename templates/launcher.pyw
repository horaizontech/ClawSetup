import os
import sys
import subprocess
import webbrowser
import threading
from pathlib import Path

# Try to import tray dependencies, auto-install if missing
try:
    from PIL import Image, ImageDraw
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pystray", "Pillow"], check=True)
        from PIL import Image, ImageDraw
        import pystray
        TRAY_AVAILABLE = True
    except Exception:
        TRAY_AVAILABLE = False

# Load environment variables manually to avoid extra dependencies in launcher
env_path = Path(__file__).parent / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key] = val

PORT = env_vars.get("OPENCLAW_PORT", "18789")
TOKEN = env_vars.get("GATEWAY_TOKEN", "")
DASHBOARD_URL = f"http://localhost:{PORT}"
if TOKEN:
    DASHBOARD_URL += f"/?token={TOKEN}"

def create_icon_image():
    """Creates a simple placeholder icon for the system tray."""
    if not TRAY_AVAILABLE: return None
    width = 64
    height = 64
    color1 = "#00F5FF"
    color2 = "#0D1117"
    
    image = Image.new('RGB', (width, height), color2)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
        fill=color1
    )
    return image

def start_docker():
    """Starts the docker-compose stack."""
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(Path(__file__).parent))

def stop_docker():
    """Stops the docker-compose stack."""
    subprocess.run(["docker", "compose", "down"], cwd=str(Path(__file__).parent))

def open_dashboard(icon=None, item=None):
    """Opens the OpenClaw dashboard in the default browser."""
    webbrowser.open(DASHBOARD_URL)

def view_logs(icon=None, item=None):
    """Opens the docker logs in a new terminal window."""
    if sys.platform == "win32":
        subprocess.Popen(["cmd.exe", "/c", "docker compose logs -f & pause"], cwd=str(Path(__file__).parent))
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "cd {Path(__file__).parent} && docker compose logs -f"'])
    else:
        subprocess.Popen(["x-terminal-emulator", "-e", "docker compose logs -f"], cwd=str(Path(__file__).parent))

def stop_app(icon=None, item=None):
    """Stops the docker containers."""
    threading.Thread(target=stop_docker).start()
    if icon:
        icon.notify("OpenClaw is stopping...", "ClawSetup")

def quit_app(icon=None, item=None):
    """Stops containers and exits the tray app."""
    if icon:
        icon.stop()
    stop_docker()
    sys.exit(0)

def main():
    # Start the backend
    start_docker()
    
    # Open browser automatically on launch
    webbrowser.open(DASHBOARD_URL)
    
    if TRAY_AVAILABLE:
        # Setup System Tray
        image = create_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", open_dashboard, default=True),
            pystray.MenuItem("View Logs", view_logs),
            pystray.MenuItem("Stop OpenClaw", stop_app),
            pystray.MenuItem("Quit", quit_app)
        )
        
        icon = pystray.Icon("OpenClaw", image, "OpenClaw AI Agent", menu)
        icon.run()
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
