import customtkinter as ctk
import threading
import time
import webbrowser
import os
import shutil
import platform
import subprocess
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

        self.after(1000, self.start_install)

    def log(self, text):
        self.after(0, self._do_log, text)

    def _do_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_install(self):
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
            telegram = data.get("telegram_enabled", False)

            # 1. Directories
            self.log(f"Creating directory structure at {install_dir}...")
            install_dir.mkdir(parents=True, exist_ok=True)
            for d in ["workspace", "agents", "logs", "assets"]: (install_dir / d).mkdir(exist_ok=True)
            self.progress.set(0.1)

            # 2. Icons
            self.log("Saving icons...")
            try:
                import base64
                from assets.icons import CLAW_ICO_B64, CLAW_PNG_B64
                with open(install_dir / "assets" / "claw.ico", "wb") as f: f.write(base64.b64decode(CLAW_ICO_B64))
                with open(install_dir / "assets" / "claw.png", "wb") as f: f.write(base64.b64decode(CLAW_PNG_B64))
            except Exception as e: self.log(f"Warning: {e}")

            # 3. Templates
            self.log("Copying configuration files...")
            template_dir = BASE_DIR / "templates"
            for f_name in ["docker-compose.yml", "launcher.pyw", "telegram_notifier.py"]:
                if (template_dir / f_name).exists(): shutil.copy(template_dir / f_name, install_dir / f_name)
            self.progress.set(0.2)

            # 4. .env
            self.log("Writing .env file...")
            env_content = f"WORKSPACE_BASE={install_dir / 'workspace'}\nOPENCLAW_PORT={port}\nOPENCLAW_IMAGE={OPENCLAW_IMAGE}\nOLLAMA_API_URL=http://127.0.0.1:11434/api\nDEFAULT_AGENT={agents[0] if agents else 'FullStack Dev'}\nDEFAULT_MODEL={models[0] if models else 'llama3.2:8b'}\n"
            with open(install_dir / ".env", "w") as f: f.write(env_content)
            self.progress.set(0.3)

            # 5. Pull Image
            self.log(f"Pulling {OPENCLAW_IMAGE}...")
            docker_manager.pull_image(OPENCLAW_IMAGE, self.log)
            self.progress.set(0.5)

            # 6. Agent Profiles
            self.log("Copying agent profiles...")
            if (template_dir / "agents").exists():
                for af in (template_dir / "agents").glob("*.json"): shutil.copy(af, install_dir / "agents" / af.name)
            self.progress.set(0.6)

            # 7. Shortcut & Firewall
            self.log("Creating desktop shortcut...")
            shortcut_creator.create_desktop_shortcut(str(install_dir / "launcher.pyw"), "OpenClaw")
            if platform.system() == "Windows":
                try:
                    from platforms.windows.firewall_windows import configure_firewall
                    configure_firewall(port, self.log)
                except Exception: pass
            self.progress.set(0.7)

            # 8. State
            self.log("Saving installation state...")
            state_data = {"installed": True, "install_dir": str(install_dir), "port": port}
            with open(INSTALL_STATE_FILE, "w") as f: json.dump(state_data, f)
            self.progress.set(0.8)

            # 9. Start Containers
            self.log("Starting OpenClaw container...")
            try: subprocess.run(["docker", "compose", "up", "-d"], cwd=str(install_dir), check=True, capture_output=True)
            except Exception as e: self.log(f"Warning: {e}")
            self.progress.set(1.0)

            self.log("Installation complete!")
            self.title.configure(text="✅ OpenClaw is ready!", text_color=SUCCESS_COLOR)
            self.btn_dashboard.configure(state="normal")
            self.btn_folder.configure(state="normal")
            self.btn_finish.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.title.configure(text="❌ Installation Failed", text_color=ERROR_COLOR)
            self.btn_finish.configure(state="normal", fg_color=ERROR_COLOR, text_color=BG_COLOR)

    def finish_wizard(self):
        self.app.load_screen("manage")

    def open_dashboard(self):
        port = self.app.install_data.get("port", 3000)
        webbrowser.open(f"http://localhost:{port}")

    def open_folder(self):
        path = self.app.install_data.get("install_dir", ".")
        if platform.system() == "Windows": os.startfile(path)
        else: subprocess.Popen(["open", path])
