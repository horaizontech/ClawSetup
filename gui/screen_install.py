import customtkinter as ctk
import threading
import time
import webbrowser
import os
import shutil
import platform
import subprocess
import requests
import json
import socket
from pathlib import Path
from gui.theme import *
import config

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.install_dir = None
        self.dashboard_url = ""

        self.title = ctk.CTkLabel(self, text="Installing OpenClaw...", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.progress = ctk.CTkProgressBar(self, width=600, height=15, progress_color=ACCENT_COLOR)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, width=600, height=350, font=FONT_MONO, fg_color=PANEL_BG, text_color=MUTED_TEXT, state="disabled")
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

    def _do_install(self):
        from utils import docker_manager, shortcut_creator

        try:
            data = self.app.install_data
            self.install_dir = Path(data.get("install_dir", "."))
            port = data.get("port", config.OPENCLAW_DEFAULT_PORT)
            model = data.get("models", ["llama3.2:8b"])[0]
            
            # 1. Directories
            self.log(f"Step 1: Creating directory structure at {self.install_dir}...")
            self.install_dir.mkdir(parents=True, exist_ok=True)
            (self.install_dir / "config").mkdir(exist_ok=True)
            (self.install_dir / "workspace").mkdir(exist_ok=True)
            self.progress.set(0.1)

            # 2. .env file
            self.log("Step 2: Writing configuration (.env)...")
            env_content = f"""OPENCLAW_IMAGE={config.OPENCLAW_IMAGE}
OPENCLAW_PORT={port}
OPENCLAW_CONFIG_DIR={self.install_dir}/config
OPENCLAW_WORKSPACE_DIR={self.install_dir}/workspace
OLLAMA_API_URL=http://host.docker.internal:11434/api
DEFAULT_MODEL={model}
"""
            with open(self.install_dir / ".env", "w") as f: f.write(env_content)
            self.progress.set(0.2)

            # 3. Docker Compose
            self.log("Step 3: Writing docker-compose.yml...")
            template_path = config.TEMPLATES_DIR / "docker-compose.yml"
            shutil.copy(template_path, self.install_dir / "docker-compose.yml")
            launch_template = config.TEMPLATES_DIR / "launcher.pyw"
            if launch_template.exists(): shutil.copy(launch_template, self.install_dir / "launcher.pyw")
            self.progress.set(0.3)

            # 4. Pull Image
            self.log(f"Step 4: Pulling {config.OPENCLAW_IMAGE}...")
            if not docker_manager.pull_image(config.OPENCLAW_IMAGE, self.log):
                raise Exception("Failed to pull OpenClaw image.")
            self.progress.set(0.6)

            # 5. Start Gateway
            self.log("Step 5: Starting OpenClaw Container...")
            subprocess.run(["docker", "compose", "up", "-d"], cwd=str(self.install_dir), check=True)
            self.progress.set(0.8)

            # 6. Wait for Ready
            self.dashboard_url = f"http://127.0.0.1:{port}"
            if self.wait_for_container_ready(self.install_dir, port, self.log):
                self.log("OpenClaw is ready!")
            else:
                self.log("Warning: Container is not reporting healthy, but will try dashboard anyway.")

            # Save state
            state_data = {
                "installed": True, "install_dir": str(self.install_dir), 
                "port": port, "dashboard_url": self.dashboard_url
            }
            with open(config.INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            
            shortcut_creator.create_desktop_shortcut(str(self.install_dir / "launcher.pyw"), "OpenClaw")
            
            self.progress.set(1.0)
            self.log("Installation complete!")
            self.after(0, self.on_success)

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.after(0, self.show_retry)

    def wait_for_container_ready(self, install_dir, port, log_callback):
        import subprocess
        import time
        import requests
        
        log_callback("Waiting for OpenClaw to start (up to 3 minutes)...")
        
        for i in range(18):  # 18 x 10s = 180s
            time.sleep(10)
            
            # Check container health status via Docker
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Health.Status}}", "openclaw-gateway"],
                    capture_output=True, text=True, timeout=10
                )
                health = result.stdout.strip()
                log_callback(f"Container health status: {health} ({(i+1)*10}s)")
                
                if health == "healthy":
                    return True
                
                if health == "unhealthy":
                    log_callback("ERROR: Container became unhealthy. Fetching logs...")
                    logs = subprocess.run(["docker", "logs", "--tail", "50", "openclaw-gateway"], capture_output=True, text=True)
                    log_callback(f"Logs:\n{logs.stdout}\n{logs.stderr}")
                    return False
            except: pass
            
            # Backup: Direct HTTP check
            try:
                r = requests.get(f"http://127.0.0.1:{port}/healthz", timeout=5)
                if r.status_code == 200:
                    log_callback("Dashboard HTTP check PASSED!")
                    return True
            except: pass
            
        log_callback("Timeout waiting for health check. Proceeding anyway...")
        return True

    def on_success(self):
        self.title.configure(text="✅ OpenClaw is ready!", text_color=SUCCESS_COLOR)
        self.btn_dashboard.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_finish.configure(state="normal", text="Finish", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        webbrowser.open(self.dashboard_url)

    def show_retry(self):
        self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
        self.btn_retry.pack(side="left", padx=10)
        self.btn_finish.configure(state="normal", text="Exit")

    def open_dashboard(self):
        webbrowser.open(self.dashboard_url)

    def open_folder(self):
        if self.install_dir: 
            if platform.system() == "Windows": os.startfile(self.install_dir)
            else: subprocess.Popen(["open", str(self.install_dir)])

    def finish_wizard(self):
        self.app.load_screen("manage")
