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
from config import BASE_DIR, OPENHANDS_IMAGE, OPENHANDS_RUNTIME_IMAGE, INSTALL_STATE_FILE

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.install_dir = None

        self.title = ctk.CTkLabel(self, text="Installing OpenHands...", font=FONT_HEADING, text_color=TEXT_COLOR)
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
        self.title.configure(text="Installing OpenHands...", text_color=TEXT_COLOR)
        self.btn_finish.configure(state="disabled")
        threading.Thread(target=self._do_install, daemon=True).start()

    def check_port_available(self, port, log_callback):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', int(port)))
        sock.close()
        if result == 0:
            log_callback(f"WARNING: Port {port} is already in use. Finding alternative...")
            # Find next available port
            for p in range(3000, 3100):
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
        self.log("Starting OpenHands container...")
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
        
        # Check running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=openhands-app", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Container status:\n{result.stdout}")
        
        # Logs
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "openhands-app"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Container logs STDOUT:\n{result.stdout}")
        log_callback(f"Container logs STDERR:\n{result.stderr}")
        
        # Port
        result = subprocess.run(
            ["docker", "port", "openhands-app"],
            capture_output=True, text=True, timeout=10
        )
        log_callback(f"Port mappings:\n{result.stdout}")

    def _do_install(self):
        from utils import docker_manager, shortcut_creator

        try:
            data = self.app.install_data
            self.install_dir = Path(data.get("install_dir", "."))
            raw_port = data.get("port", 3000)
            models = data.get("models", [])
            agents = data.get("agents", [])
            
            # 1. Pre-flight port check
            port = self.check_port_available(raw_port, self.log)
            self.app.install_data["port"] = port

            # 2. Ensure Docker is running
            if not docker_manager.ensure_docker_running(log_callback=self.log):
                self.log("ERROR: Installation halted. Docker must be running to proceed.")
                self.after(0, self.show_retry)
                return

            self.progress.set(0.1)
            # 3. Directories
            self.log(f"Creating directory structure at {self.install_dir}...")
            self.install_dir.mkdir(parents=True, exist_ok=True)
            for d in ["workspace", "agents", "logs", "assets", ".openhands-state"]: (self.install_dir / d).mkdir(exist_ok=True)
            self.progress.set(0.2)

            # 4. Templates & Env
            self.log("Setting up configuration...")
            template_dir = BASE_DIR / "templates"
            for f_name in ["docker-compose.yml", "launcher.pyw", "telegram_notifier.py"]:
                if (template_dir / f_name).exists(): 
                    shutil.copy(template_dir / f_name, self.install_dir / f_name)
            
            # Write standardized .env
            env_content = f"""OPENCLAW_PORT={port}
INSTALL_DIR={self.install_dir}
WORKSPACE_BASE={self.install_dir / 'workspace'}
SANDBOX_USER_ID=1000
OLLAMA_MODEL={models[0] if models else 'llama3.2:8b'}
TELEGRAM_TOKEN={data.get('telegram_token', '')}
TELEGRAM_CHAT_ID={data.get('telegram_chat_id', '')}
OLLAMA_API_URL=http://host.docker.internal:11434/api
"""
            with open(self.install_dir / ".env", "w") as f: f.write(env_content)
            self.progress.set(0.4)

            # 5. Pull Images
            self.log(f"Pulling OpenHands App: {OPENHANDS_IMAGE}...")
            if not docker_manager.pull_image(OPENHANDS_IMAGE, self.log):
                raise Exception("Failed to pull OpenHands app image.")
            
            self.log(f"Pulling OpenHands Runtime: {OPENHANDS_RUNTIME_IMAGE}...")
            if not docker_manager.pull_image(OPENHANDS_RUNTIME_IMAGE, self.log):
                raise Exception("Failed to pull OpenHands runtime image.")
            self.progress.set(0.7)

            # 6. Shortcut
            self.log("Finalizing installation...")
            shortcut_creator.create_desktop_shortcut(str(self.install_dir / "launcher.pyw"), "OpenHands")
            self.progress.set(0.8)

            # 7. State
            state_data = {
                "installed": True, 
                "install_dir": str(self.install_dir), 
                "port": port
            }
            with open(INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            self.progress.set(0.9)

            # 8. Start Containers
            if not self.validate_compose_file(self.install_dir):
                raise Exception("Compose file validation failed.")

            if not self.start_container(self.install_dir):
                raise Exception("Docker Compose up failed.")

            self.progress.set(1.0)
            self.log("Installation complete!")
            self.diagnose_container(self.install_dir, self.log)
            self.after(0, self.on_success)
            
            threading.Thread(target=self.open_dashboard, daemon=True).start()

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.after(0, self.show_retry)

    def show_retry(self):
        self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
        self.btn_retry.pack(side="left", padx=10)
        self.btn_finish.configure(state="normal", text="Exit")

    def on_success(self):
        self.title.configure(text="✅ OpenHands is ready!", text_color=SUCCESS_COLOR)
        self.btn_dashboard.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_finish.configure(state="normal", text="Finish", fg_color=ACCENT_COLOR, text_color=BG_COLOR)

    def get_port_from_state(self):
        try:
            if INSTALL_STATE_FILE.exists():
                state = json.loads(INSTALL_STATE_FILE.read_text())
                return state.get("port", 3000)
        except Exception: pass
        return 3000

    def open_dashboard(self):
        port = self.get_port_from_state()
        url = f"http://localhost:{port}"
        
        self.log(f"Waiting for OpenHands dashboard at {url}")
        self.log("This can take 60-90 seconds on first run...")
        
        for i in range(18):  # 18 x 10 seconds = 3 minutes
            try:
                r = requests.get(url, timeout=5)
                if r.status_code < 500:
                    self.log(f"Dashboard ready! Opening {url}")
                    webbrowser.open(url)
                    return
            except Exception:
                pass
            self.log(f"Still starting... ({(i+1)*10}s / 180s)")
            time.sleep(10)
        
        self.log(f"Opening {url} — may still be loading, please wait")
        webbrowser.open(url)

    def open_folder(self):
        path = self.install_dir or self.app.install_data.get("install_dir", ".")
        if platform.system() == "Windows": os.startfile(path)
        else: subprocess.Popen(["open", path])

    def finish_wizard(self):
        self.app.load_screen("manage")
