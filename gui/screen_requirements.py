import customtkinter as ctk
import threading
import platform
import shutil
import socket
import subprocess
from gui.theme import *
from utils import system_check, drive_selector
import config

class RequirementsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.requirements_met = False

        self.title = ctk.CTkLabel(self, text="System Requirements", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_BG, width=600, height=350)
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.items = {}
        self.setup_checklist()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_prev = ctk.CTkButton(
            btn_frame, text="Back", command=lambda: self.app.load_screen("welcome"),
            fg_color=PANEL_BG, text_color=TEXT_COLOR
        )
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            btn_frame, text="Next", command=lambda: self.app.load_screen("drive"), state="disabled",
            fg_color=PANEL_BG, text_color=MUTED_TEXT
        )
        self.btn_next.pack(side="left", padx=10)

        # Auto-run checks
        self.after(500, self.run_checks)

    def setup_checklist(self):
        reqs = [
            ("node", f"Node.js {config.NODE_REQUIRED_VERSION}+"),
            ("python", "Python 3.11+"),
            ("git", "Git"),
            ("ram", "8GB RAM Minimum"),
            ("disk", "Sufficient storage found"),
            ("internet", "Internet Connectivity")
        ]

        for key, name in reqs:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            lbl = ctk.CTkLabel(row, text=name, font=FONT_MAIN, text_color=TEXT_COLOR, width=200, anchor="w")
            lbl.pack(side="left", padx=10)
            
            status = ctk.CTkLabel(row, text="⏳ Checking...", font=FONT_MAIN, text_color=ACCENT_COLOR)
            status.pack(side="left", padx=10)
            
            btn = ctk.CTkButton(row, text="Auto-Install", width=100, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
            if key == "node" and platform.system() == "Windows":
                btn.configure(command=self.install_node)
            else:
                btn.configure(state="disabled")
            
            self.items[key] = {"label": lbl, "status": status, "btn": btn, "row": row}

    def install_node(self):
        self.items["node"]["btn"].configure(state="disabled", text="Downloading...")
        # This will be handled in screen_install if missing, but we can offer it here too
        threading.Thread(target=self._do_install_node, daemon=True).start()

    def _do_install_node(self):
        # We'll use the logic from the user's request
        import urllib.request
        from pathlib import Path
        try:
            url = "https://nodejs.org/dist/latest-v22.x/node-v22.14.0-x64.msi"
            installer_path = Path.home() / "Downloads" / "node-installer.msi"
            urllib.request.urlretrieve(url, installer_path)
            self.after(0, lambda: self.items["node"]["btn"].configure(text="Installing..."))
            subprocess.run(["msiexec", "/i", str(installer_path), "/quiet", "/norestart"], check=True)
            self.after(0, lambda: self._update_status("node", True, "✅ Installed (Needs Restart)"))
        except Exception as e:
            self.after(0, lambda: self._update_status("node", False, f"❌ Failed: {str(e)[:20]}"))

    def _update_status(self, key, passed, text):
        status_lbl = self.items[key]["status"]
        btn = self.items[key]["btn"]
        if passed:
            status_lbl.configure(text=text, text_color=SUCCESS_COLOR)
            if btn.winfo_exists():
                btn.pack_forget()
        else:
            status_lbl.configure(text="❌ Missing", text_color=ERROR_COLOR)
            btn.pack(side="right", padx=10)
            btn.configure(state="normal", text="Retry")
        self.check_all_passed()

    def check_all_passed(self):
        all_passed = True
        for key, item in self.items.items():
            current_text = item["status"].cget("text")
            if "❌" in current_text or "⏳" in current_text:
                all_passed = False
                break
        if all_passed:
            self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        else:
            self.btn_next.configure(state="disabled", fg_color=PANEL_BG, text_color=MUTED_TEXT)

    def run_checks(self):
        threading.Thread(target=self._perform_checks, daemon=True).start()

    def _perform_checks(self):
        # 1. Connectivity Check
        internet = False
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            internet = True
        except OSError:
            pass

        # 2. Disk Space Check
        drives = drive_selector.get_mounted_drives()
        disk_ok = any(d["free_gb"] >= 2.0 for d in drives)

        results = {
            "node": system_check.check_node_version() >= config.NODE_REQUIRED_VERSION,
            "python": system_check.check_python(),
            "git": system_check.check_git(),
            "ram": system_check.get_ram_info()["total_gb"] >= 8.0,
            "disk": disk_ok,
            "internet": internet
        }

        for key, passed in results.items():
            text = "✅ Found" if passed else "❌ Missing"
            if key == "node" and passed:
                v = system_check.check_node_version()
                text = f"✅ v{v}"
            self.after(0, lambda k=key, p=passed, t=text: self._update_status(k, p, t))
