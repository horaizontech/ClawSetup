import customtkinter as ctk
import threading
import time
import webbrowser
import os
import shutil
import platform
import subprocess
import requests
import secrets
import json
import socket
import re
from pathlib import Path
from gui.theme import *
from config import BASE_DIR, OPENCLAW_IMAGE

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.install_dir = None

        self.title = ctk.CTkLabel(self, text="Installing OpenClaw...", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.progress = ctk.CTkProgressBar(self, width=600, height=15, progress_color=ACCENT_COLOR)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, width=600, height=300, font=FONT_MONO, fg_color=PANEL_BG, text_color=MUTED_TEXT, state="disabled")
        self.log_box.pack(pady=10, padx=20)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)

        self.btn_dashboard = ctk.CTkButton(self.btn_frame, text="Open Dashboard", command=self.open_dashboard, fg_color=SUCCESS_COLOR, text_color=BG_COLOR, state="disabled")
        self.btn_dashboard.pack(side="left", padx=10)

        self.btn_folder = ctk.CTkButton(self.btn_frame, text="Open Install Folder", command=self.open_folder, fg_color=PANEL_BG, text_color=TEXT_COLOR, state="disabled")
        self.btn_folder.pack(side="left", padx=10)

        self.btn_finish = ctk.CTkButton(self.btn_frame, text="Finish", command=self.finish_wizard, fg_color=PANEL_BG, text_color=TEXT_COLOR, state="disabled")
        self.btn_finish.pack(side="left", padx=10)
        
        self.btn_retry = ctk.CTkButton(self.btn_frame, text="Retry", command=self.start_install, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        
        self.after(1000, self.start_install)

    def log(self, text):
        self.after(0, self._do_log, text)

    def _do_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_install(self):
        self.btn_retry.pack_forget()
        self.title.configure(text="Installing OpenClaw...", text_color=TEXT_COLOR)
        self.btn_finish.configure(state="disabled")
        threading.Thread(target=self._do_install, daemon=True).start()

    def check_port_available(self, port, log_callback):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', int(port)))
        sock.close()
        if result == 0:
            log_callback(f"WARNING: Port {port} is already in use. Finding alternative...")
            # Find next available port
            for p in range(18789, 18900):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                r = s.connect_ex(('localhost', p))
                s.close()
                if r != 0:
                    log_callback(f"Using port {p} instead")
                    return p
        return port

    def validate_compose_file(self, install_dir):
        compose_path = Path(install_dir) / "docker-compose.yml"
        if not compose_path.exists():
            self.log(f"ERROR: docker-compose.yml not found at {compose_path}")
            return False
        
        # Check file is not empty
        content = compose_path.read_text()
        if len(content.strip()) < 10:
            self.log(f"ERROR: docker-compose.yml is empty")
            return False
        
        self.log(f"docker-compose.yml found at {compose_path}")
        
        env_path = Path(install_dir) / ".env"
        if not env_path.exists():
            self.log("ERROR: .env file not found next to docker-compose.yml")
            return False

        return True

    def start_container(self, install_dir):
        self.log("Starting OpenClaw container...")
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            cwd=str(install_dir)
        )
        if result.returncode != 0:
            self.log(f"Docker Compose STDOUT: {result.stdout}")
            self.log(f"Docker Compose STDERR: {result.stderr}")
            return False
        return True

    def diagnose_container(self, install_dir, log_callback):
        self.log("Running container diagnostics...")
        import subprocess
        
        # Check 1: Is the container actually running?
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=openclaw-gateway", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Container status:\n{result.stdout}")
        
        # Check 2: What are the container logs?
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "openclaw-gateway"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Container logs STDOUT:\n{result.stdout}")
        log_callback(f"Container logs STDERR:\n{result.stderr}")
        
        # Check 3: What ports are actually exposed?
        result = subprocess.run(
            ["docker", "port", "openclaw-gateway"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Port mappings:\n{result.stdout}")
        
        # Check 4: Inspect the container
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}} - {{.State.Error}}", "openclaw-gateway"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Container inspect: {result.stdout}")

    def _do_install(self):
        from utils import docker_manager, shortcut_creator
        from main import INSTALL_STATE_FILE

        try:
            data = self.app.install_data
            self.install_dir = Path(data.get("install_dir", "."))
            raw_port = data.get("port", 18789)
            models = data.get("models", [])
            agents = data.get("agents", [])
            
            # 1. Pre-flight port check
            port = self.check_port_available(raw_port, self.log)
            self.app.install_data["port"] = port

            # Generate security token
            gateway_token = secrets.token_urlsafe(32)
            self.app.install_data["gateway_token"] = gateway_token

            # 2. Ensure Docker is running
            if not docker_manager.ensure_docker_running(log_callback=self.log):
                self.log("ERROR: Installation halted. Docker must be running to proceed.")
                self.after(0, self.show_retry)
                return

            self.progress.set(0.1)
            # 3. Directories
            self.log(f"Creating directory structure at {self.install_dir}...")
            self.install_dir.mkdir(parents=True, exist_ok=True)
            for d in ["workspace", "agents", "logs", "assets", ".openclaw"]: (self.install_dir / d).mkdir(exist_ok=True)
            self.progress.set(0.2)

            # 4. Templates & Env
            self.log("Setting up configuration...")
            template_dir = BASE_DIR / "templates"
            for f_name in ["docker-compose.yml", "launcher.pyw", "telegram_notifier.py"]:
                if (template_dir / f_name).exists(): 
                    shutil.copy(template_dir / f_name, self.install_dir / f_name)
            
            # Write standardized .env
            env_content = f"""OPENCLAW_PORT={port}
GATEWAY_TOKEN={gateway_token}
INSTALL_DIR={self.install_dir}
OLLAMA_MODEL={models[0] if models else 'llama3.2:8b'}
TELEGRAM_TOKEN={data.get('telegram_token', '')}
TELEGRAM_CHAT_ID={data.get('telegram_chat_id', '')}
WORKSPACE_BASE={self.install_dir / 'workspace'}
OPENCLAW_IMAGE={OPENCLAW_IMAGE}
OLLAMA_API_URL=http://127.0.0.1:11434/api
DEFAULT_AGENT={agents[0] if agents else 'FullStack Dev'}
DEFAULT_MODEL={models[0] if models else 'llama3.2:8b'}
"""
            with open(self.install_dir / ".env", "w") as f: f.write(env_content)
            self.progress.set(0.4)

            # 5. Pull Image
            self.log(f"Pulling {OPENCLAW_IMAGE}...")
            if not docker_manager.pull_image(OPENCLAW_IMAGE, self.log):
                raise Exception("Failed to pull Docker image.")
            self.progress.set(0.7)

            # 6. Agent Profiles & Shortcut
            self.log("Finalizing installation...")
            if (template_dir / "agents").exists():
                for af in (template_dir / "agents").glob("*.json"): shutil.copy(af, self.install_dir / "agents" / af.name)
            
            shortcut_creator.create_desktop_shortcut(str(self.install_dir / "launcher.pyw"), "OpenClaw")
            self.progress.set(0.8)

            # 7. State
            state_data = {
                "installed": True, 
                "install_dir": str(self.install_dir), 
                "port": port,
                "gateway_token": gateway_token
            }
            with open(INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            self.progress.set(0.9)

            # 8. Start Containers
            if not self.validate_compose_file(self.install_dir):
                raise Exception("Compose file validation failed.")

            if not self.start_container(self.install_dir):
                raise Exception("Docker Compose up failed. See logs above.")

            self.progress.set(1.0)
            self.log("Installation complete!")
            
            # Run diagnostics
            self.diagnose_container(self.install_dir, self.log)
            
            self.after(0, self.on_success)
            
            # Non-blocking dashboard open attempt
            threading.Thread(target=self.open_dashboard, daemon=True).start()

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.after(0, self.show_retry)

    def show_retry(self):
        self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
        self.btn_retry.pack(side="left", padx=10)
        self.btn_finish.configure(state="normal", text="Exit")

    def on_success(self):
        self.title.configure(text="✅ OpenClaw is ready!", text_color=SUCCESS_COLOR)
        self.btn_dashboard.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_finish.configure(state="normal", text="Finish", fg_color=ACCENT_COLOR, text_color=BG_COLOR)

    def open_dashboard(self):
        from main import INSTALL_STATE_FILE
        install_dir = self.install_dir or self.app.install_data.get("install_dir")
        port = self.app.install_data.get("port") or 18789
        
        self.log("Getting dashboard URL from OpenClaw...")
        
        # Method 1: Get tokenized URL directly from openclaw-cli
        try:
            result = subprocess.run(
                ["docker", "compose", "run", "--rm", "openclaw-cli", "dashboard", "--no-open"],
                capture_output=True,
                text=True,
                cwd=str(install_dir),
                timeout=30
            )
            output = result.stdout + result.stderr
            url_match = re.search(r'http://[^\s]+token=[^\s]+', output)
            if url_match:
                dashboard_url = url_match.group(0)
                # Cleanup potential formatting
                dashboard_url = dashboard_url.replace("\n", "").replace("\r", "")
                self.log(f"Dashboard URL found: {dashboard_url}")
                self.save_dashboard_url(dashboard_url)
                webbrowser.open(dashboard_url)
                return
        except Exception as e:
            self.log(f"Could not get URL from CLI: {e}")
        
        # Method 2: Read token from .env and build URL manually
        try:
            env_path = Path(install_dir) / ".env"
            if env_path.exists():
                env_content = env_path.read_text()
                token = None
                for line in env_content.splitlines():
                    if line.startswith("GATEWAY_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        break
                
                if token:
                    dashboard_url = f"http://127.0.0.1:{port}/?token={token}"
                    self.log(f"Using token from .env: {dashboard_url}")
                    self.log("Waiting for dashboard to be ready...")
                    for i in range(12):
                        try:
                            r = requests.get(f"http://127.0.0.1:{port}", timeout=5)
                            if r.status_code < 500:
                                self.log("Dashboard is ready!")
                                webbrowser.open(dashboard_url)
                                return
                        except Exception:
                            pass
                        self.log(f"Still starting... ({(i+1)*5}s)")
                        time.sleep(5)
                    
                    self.log("Opening dashboard (may still be loading)...")
                    webbrowser.open(dashboard_url)
                    return
        except Exception as e:
            self.log(f"Could not read token from .env: {e}")
        
        # Method 3: Fallback
        self.log("WARNING: Could not get token automatically")
        self.log(f"Please open http://127.0.0.1:{port} and enter your token manually")
        self.log(f"Your token is in: {install_dir}\\.env")
        webbrowser.open(f"http://127.0.0.1:{port}")

    def save_dashboard_url(self, url):
        from main import INSTALL_STATE_FILE
        install_dir = self.install_dir or self.app.install_data.get("install_dir")
        if not install_dir: return
        state_file = Path(install_dir) / "install_state.json"
        try:
            if state_file.exists():
                state = json.loads(state_file.read_text())
            else:
                state = {}
            state["dashboard_url"] = url
            state_file.write_text(json.dumps(state, indent=2))
        except Exception as e:
            self.log(f"Could not save dashboard URL: {e}")

    def open_folder(self):
        path = self.app.install_data.get("install_dir", ".")
        if platform.system() == "Windows": os.startfile(path)
        else: subprocess.Popen(["open", path])

    def finish_wizard(self):
        self.app.load_screen("manage")
