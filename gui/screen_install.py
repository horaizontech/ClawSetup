import customtkinter as ctk
import threading
import time
import webbrowser
import os
import shutil
import platform
import subprocess
import requests
from pathlib import Path
from gui.theme import *
from config import BASE_DIR, OPENCLAW_IMAGE

class InstallScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

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
        # Hidden by default
        
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
        from utils import docker_manager, shortcut_creator, health_check
        from main import INSTALL_STATE_FILE
        import json

        try:
            data = self.app.install_data
            install_dir = Path(data.get("install_dir", "."))
            port = data.get("port", 3000)
            models = data.get("models", [])
            agents = data.get("agents", [])

            # 1. Ensure Docker is running (v. critical)
            if not docker_manager.ensure_docker_running(log_callback=self.log):
                self.log("ERROR: Installation halted. Docker must be running to proceed.")
                self.after(0, self.show_retry)
                return

            self.progress.set(0.1)
            # 2. Directories
            self.log(f"Creating directory structure at {install_dir}...")
            install_dir.mkdir(parents=True, exist_ok=True)
            for d in ["workspace", "agents", "logs", "assets"]: (install_dir / d).mkdir(exist_ok=True)
            self.progress.set(0.2)

            # 3. Templates & Env
            self.log("Setting up configuration...")
            template_dir = BASE_DIR / "templates"
            for f_name in ["docker-compose.yml", "launcher.pyw", "telegram_notifier.py"]:
                if (template_dir / f_name).exists(): shutil.copy(template_dir / f_name, install_dir / f_name)
            
            env_content = f"WORKSPACE_BASE={install_dir / 'workspace'}\nOPENCLAW_PORT={port}\nOPENCLAW_IMAGE={OPENCLAW_IMAGE}\nOLLAMA_API_URL=http://127.0.0.1:11434/api\nDEFAULT_AGENT={agents[0] if agents else 'FullStack Dev'}\nDEFAULT_MODEL={models[0] if models else 'llama3.2:8b'}\n"
            with open(install_dir / ".env", "w") as f: f.write(env_content)
            self.progress.set(0.4)

            # 4. Pull Image
            self.log(f"Pulling {OPENCLAW_IMAGE} (this takes a while)...")
            if not docker_manager.pull_image(OPENCLAW_IMAGE, self.log):
                raise Exception("Failed to pull Docker image.")
            self.progress.set(0.7)

            # 5. Agent Profiles & Shortcut
            self.log("Finalizing installation...")
            if (template_dir / "agents").exists():
                for af in (template_dir / "agents").glob("*.json"): shutil.copy(af, install_dir / "agents" / af.name)
            
            shortcut_creator.create_desktop_shortcut(str(install_dir / "launcher.pyw"), "OpenClaw")
            if platform.system() == "Windows":
                try:
                    from platforms.windows.firewall_windows import configure_firewall
                    configure_firewall(port, self.log)
                except Exception: pass
            
            # 6. State
            state_data = {"installed": True, "install_dir": str(install_dir), "port": port}
            with open(INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            self.progress.set(0.9)

            # 7. Start Containers
            self.log("Starting OpenClaw container...")
            subprocess.run(["docker", "compose", "up", "-d"], cwd=str(install_dir), check=True, capture_output=True)
            self.progress.set(1.0)

            self.log("Installation complete!")
            self.after(0, self.on_success)

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
        def _wait_and_open():
            from main import INSTALL_STATE_FILE
            import json
            
            # Resolve port
            port = self.app.install_data.get("port")
            if not port:
                if INSTALL_STATE_FILE.exists():
                    try:
                        with open(INSTALL_STATE_FILE, "r") as f:
                            state = json.load(f)
                            port = state.get("port")
                    except Exception: pass
            if not port: port = 3000
            
            url = f"http://localhost:{port}"
            self.log("Waiting for OpenClaw dashboard to start...")
            
            for i in range(12): # 60 seconds
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code < 500:
                        self.log(f"Dashboard is ready at {url}")
                        webbrowser.open(url)
                        return
                except Exception:
                    self.log(f"Dashboard starting... ({(i+1)*5}s)")
                    time.sleep(5)
            
            self.log(f"Opening {url} — dashboard may still be loading")
            webbrowser.open(url)

        threading.Thread(target=_wait_and_open, daemon=True).start()

    def finish_wizard(self):
        self.app.load_screen("manage")

    def open_folder(self):
        path = self.app.install_data.get("install_dir", ".")
        if platform.system() == "Windows": os.startfile(path)
        else: subprocess.Popen(["open", path])
