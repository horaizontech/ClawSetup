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
import config

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.install_dir = None
        self.dashboard_url = ""

        # Yellow Info Banner
        self.info_banner = ctk.CTkFrame(self, fg_color="#FFF9C4", height=50) # Light yellow
        self.info_banner.pack(fill="x", padx=20, pady=(10, 0))
        self.info_label = ctk.CTkLabel(
            self.info_banner, 
            text="⚠️ OpenClaw requires a one-time setup. This installer will handle it automatically.\nFirst run may take 2-3 minutes.",
            text_color="#FBC02D", font=("Roboto", 12, "bold")
        )
        self.info_label.pack(pady=5)

        self.title = ctk.CTkLabel(self, text="Installing OpenClaw...", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.progress = ctk.CTkProgressBar(self, width=600, height=15, progress_color=ACCENT_COLOR)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, width=600, height=300, font=FONT_MONO, fg_color=PANEL_BG, text_color=MUTED_TEXT, state="disabled")
        self.log_box.pack(pady=10, padx=20)

        # Copyable URL Frame (Hidden until success)
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        
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
            # Also copy launcher
            launch_template = config.TEMPLATES_DIR / "launcher.pyw"
            if launch_template.exists(): shutil.copy(launch_template, self.install_dir / "launcher.pyw")
            self.progress.set(0.3)

            # 4. Pull Image
            self.log(f"Step 4: Pulling {config.OPENCLAW_IMAGE}...")
            if not docker_manager.pull_image(config.OPENCLAW_IMAGE, self.log):
                raise Exception("Failed to pull OpenClaw image.")
            self.progress.set(0.5)

            # 5. Onboarding
            self.log("Step 5: Running mandatory onboarding (one-time setup)...")
            onboard_cmd = ["docker", "compose", "run", "--rm", "openclaw-cli", "onboard", "--yes"]
            result = subprocess.run(onboard_cmd, capture_output=True, text=True, cwd=str(self.install_dir), timeout=180)
            if result.returncode != 0:
                self.log("Note: Non-interactive onboarding with --yes failed. Retrying without TTY...")
                onboard_cmd = ["docker", "compose", "run", "--rm", "-T", "openclaw-cli", "onboard"]
                result = subprocess.run(onboard_cmd, capture_output=True, text=True, cwd=str(self.install_dir), timeout=180)
            
            self.log(f"Onboarding output: {result.stdout}")
            if result.stderr: self.log(f"Onboarding notes: {result.stderr}")
            self.progress.set(0.7)

            # 6. Start Gateway
            self.log("Step 6: Starting OpenClaw Gateway...")
            subprocess.run(["docker", "compose", "up", "-d", "openclaw-gateway"], cwd=str(self.install_dir), check=True)
            self.progress.set(0.8)

            # 7. Get Token
            self.log("Step 7: Retrieving dashboard token...")
            token_cmd = ["docker", "compose", "run", "--rm", "openclaw-cli", "dashboard", "--no-open"]
            result = subprocess.run(token_cmd, capture_output=True, text=True, cwd=str(self.install_dir), timeout=60)
            output = result.stdout + result.stderr
            self.log(f"Dashboard info: {output}")

            token_match = re.search(r'token[=:\s]+([A-Za-z0-9_\-\.]+)', output, re.IGNORECASE)
            url_match = re.search(r'http://[^\s]+', output)
            
            if url_match:
                self.dashboard_url = url_match.group(0).replace("\n", "").replace("\r", "")
            else:
                token = token_match.group(1) if token_match else ""
                self.dashboard_url = f"http://127.0.0.1:{port}"
                if token: self.dashboard_url += f"/?token={token}"

            self.log(f"Final Dashboard URL: {self.dashboard_url}")
            
            # Save state
            state_data = {
                "installed": True, "install_dir": str(self.install_dir), 
                "port": port, "dashboard_url": self.dashboard_url
            }
            with open(config.INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            
            shortcut_creator.create_desktop_shortcut(str(self.install_dir / "launcher.pyw"), "OpenClaw")
            self.progress.set(0.9)

            # 8. Health Check
            self.log("Step 8: Waiting for health check (healthz)...")
            health_url = f"http://127.0.0.1:{port}/healthz"
            for i in range(18): # 3 minutes
                try:
                    r = requests.get(health_url, timeout=5)
                    if r.status_code == 200:
                        self.log("OpenClaw is healthy!")
                        break
                except: pass
                self.log(f"Waiting for OpenClaw... ({(i+1)*10}s)")
                time.sleep(10)

            self.progress.set(1.0)
            self.log("Installation complete!")
            self.after(0, self.on_success)

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.after(0, self.show_retry)

    def on_success(self):
        self.info_banner.destroy()
        self.title.configure(text="✅ Installation Complete!", text_color=SUCCESS_COLOR)
        
        # Dashboard URL Display
        self.url_frame.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(self.url_frame, text="Dashboard URL (Copy this):", font=("Roboto", 10)).pack()
        url_entry = ctk.CTkEntry(self.url_frame, width=500, font=("Consolas", 11))
        url_entry.insert(0, self.dashboard_url)
        url_entry.pack(pady=5)
        ctk.CTkLabel(self.url_frame, text="Paste your token in Settings on first visit if prompted.", font=("Roboto", 10, "italic"), text_color=MUTED_TEXT).pack()

        self.btn_dashboard.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_finish.configure(state="normal", text="Finish", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        
        # Auto-open
        webbrowser.open(self.dashboard_url)

    def show_retry(self):
        self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
        self.btn_retry.pack(side="left", padx=10)
        self.btn_finish.configure(state="normal", text="Exit")

    def open_dashboard(self):
        webbrowser.open(self.dashboard_url)

    def open_folder(self):
        if self.install_dir: os.startfile(self.install_dir)

    def finish_wizard(self):
        self.app.load_screen("manage")
