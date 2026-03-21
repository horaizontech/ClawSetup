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
import urllib.request
from pathlib import Path
from gui.theme import *
import config

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.install_dir = None

        self.title = ctk.CTkLabel(self, text="Installing OpenClaw (Native)...", font=FONT_HEADING, text_color=TEXT_COLOR)
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
        try:
            # Step 1: Check/Install Node.js
            self.log("Step 1: Verifying Node.js 22+...")
            if not self.install_nodejs(self.log):
                raise Exception("Node.js installation failed.")
            self.progress.set(0.2)

            # Step 2: Install OpenClaw via npm
            self.log("Step 2: Installing OpenClaw via npm...")
            if not self.install_openclaw_npm(self.log):
                raise Exception("NPM installation failed.")
            self.progress.set(0.4)

            # Step 3: Onboarding
            self.log("Step 3: Running onboarding wizard...")
            if not self.run_onboarding(self.app.install_dir, self.log):
                self.log("Warning: Onboarding returned non-zero code. Proceeding to service setup...")
            self.progress.set(0.6)

            # Step 4: PM2 Service
            self.log("Step 4: Setting up background service...")
            self.install_pm2_service(self.log)
            self.progress.set(0.8)

            # finalize
            self.log("Finalizing installation...")
            state_data = {
                "installed": True,
                "install_dir": str(self.app.install_dir),
                "ai_provider": self.app.ai_provider,
                "port": config.OPENCLAW_GATEWAY_PORT
            }
            with open(config.INSTALL_STATE_FILE, "w") as f:
                json.dump(state_data, f)
            
            self.progress.set(1.0)
            self.log("Installation complete! Dashboard available at http://localhost:18789")
            self.after(0, self.on_success)

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.after(0, self.show_retry)

    def install_nodejs(self, log_callback):
        from utils import system_check
        version = system_check.check_node_version()
        if version >= config.NODE_REQUIRED_VERSION:
            log_callback(f"Node.js v{version} already installed ✓")
            return True
        
        log_callback(f"Node.js {config.NODE_REQUIRED_VERSION}+ not found. Downloading...")
        if platform.system() == "Windows":
            # Using the URL from user request
            url = "https://nodejs.org/dist/latest-v22.x/node-v22.14.0-x64.msi"
            installer_path = Path.home() / "Downloads" / "node-installer.msi"
            urllib.request.urlretrieve(url, installer_path)
            log_callback("Installing Node.js silently (this may take a minute)...")
            subprocess.run(["msiexec", "/i", str(installer_path), "/quiet", "/norestart"], check=True)
            log_callback("Node.js installed successfully ✓")
            return True
        return False

    def install_openclaw_npm(self, log_callback):
        log_callback("Running: npm install -g openclaw@latest")
        process = subprocess.Popen(
            ["npm", "install", "-g", "openclaw@latest"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True
        )
        for line in process.stdout: log_callback(line.strip())
        process.wait()
        return process.returncode == 0

    def run_onboarding(self, install_dir, log_callback):
        log_callback("Running OpenClaw onboarding (Native)...")
        # We try to automate common answers if possible, but for now we follow the template
        # Note: In a real scenario, we might need to send Keystrokes or use -y if available
        process = subprocess.Popen(
            ["openclaw", "onboard", "--install-daemon"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, shell=True, cwd=str(install_dir)
        )
        # We don't have interactive logic yet, just streaming output
        for line in process.stdout: log_callback(line.strip())
        process.wait()
        return process.returncode == 0

    def install_pm2_service(self, log_callback):
        log_callback("Installing PM2...")
        subprocess.run(["npm", "install", "-g", "pm2"], shell=True, capture_output=True)
        log_callback("Starting OpenClaw gateway via PM2...")
        subprocess.run(["pm2", "start", "openclaw", "--", "gateway", "--allow-unconfigured"], shell=True, capture_output=True)
        subprocess.run(["pm2", "save"], shell=True, capture_output=True)
        if platform.system() == "Windows":
            log_callback("Configuring PM2 to start on boot...")
            subprocess.run(["pm2", "startup", "windows"], shell=True, capture_output=True)

    def on_success(self):
        self.title.configure(text="✅ OpenClaw is ready!", text_color=SUCCESS_COLOR)
        self.btn_dashboard.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_finish.configure(state="normal", text="Finish", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        webbrowser.open(config.OPENCLAW_DASHBOARD_URL)

    def show_retry(self):
        self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
        self.btn_retry.pack(side="left", padx=10)
        self.btn_finish.configure(state="normal", text="Exit")

    def open_dashboard(self):
        webbrowser.open(config.OPENCLAW_DASHBOARD_URL)

    def open_folder(self):
        path = self.app.install_dir
        if platform.system() == "Windows": os.startfile(path)
        else: subprocess.Popen(["open", str(path)])

    def finish_wizard(self):
        self.app.load_screen("manage")
