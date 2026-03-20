import customtkinter as ctk
import threading
import platform
import shutil
import socket
from gui.theme import *
from utils import system_check

class ScreenRequirements(ctk.CTkFrame):
    def __init__(self, master, on_next, on_prev, **kwargs):
        super().__init__(master, fg_color=BG_COLOR, **kwargs)
        self.on_next = on_next
        self.on_prev = on_prev
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
            btn_frame, text="Back", command=self.on_prev,
            fg_color=PANEL_BG, text_color=TEXT_COLOR
        )
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            btn_frame, text="Next", command=self.on_next, state="disabled",
            fg_color=PANEL_BG, text_color=MUTED_TEXT
        )
        self.btn_next.pack(side="left", padx=10)

        # Auto-run checks
        self.after(500, self.run_checks)

    def setup_checklist(self):
        reqs = [
            ("docker", "Docker Desktop"),
            ("python", "Python 3.11+"),
            ("git", "Git"),
            ("ram", "8GB RAM Minimum"),
            ("disk", "20GB Free Disk Space"),
            ("internet", "Internet Connectivity")
        ]
        if platform.system() == "Windows":
            reqs.append(("wsl2", "WSL2 Subsystem"))

        for key, name in reqs:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            lbl = ctk.CTkLabel(row, text=name, font=FONT_MAIN, text_color=TEXT_COLOR, width=200, anchor="w")
            lbl.pack(side="left", padx=10)
            
            status = ctk.CTkLabel(row, text="⏳ Checking...", font=FONT_MAIN, text_color=ACCENT_COLOR)
            status.pack(side="left", padx=10)
            
            btn = ctk.CTkButton(row, text="Auto-Install", width=100, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
            if key == "docker":
                btn.configure(command=self.install_docker)
            elif key == "wsl2":
                btn.configure(command=self.install_wsl2)
            else:
                btn.configure(state="disabled")
            
            self.items[key] = {"label": lbl, "status": status, "btn": btn, "row": row}

    def install_docker(self):
        self.items["docker"]["btn"].configure(state="disabled", text="Installing...")
        threading.Thread(target=self._do_install_docker, daemon=True).start()

    def _do_install_docker(self):
        if platform.system() == "Windows":
            from platforms.windows import docker_windows
            success = docker_windows.install_docker(lambda m: print(f"[Docker] {m}"))
        elif platform.system() == "Darwin":
            from platforms.macos import docker_mac
            success = docker_mac.install_docker_mac(lambda m: print(f"[Docker] {m}"))
        else:
            success = False

        if success:
            self.after(0, lambda: self._update_status("docker", True, "✅ Installed"))
        else:
            self.after(0, lambda: self._update_status("docker", False, "❌ Failed"))

    def install_wsl2(self):
        self.items["wsl2"]["btn"].configure(state="disabled", text="Installing...")
        threading.Thread(target=self._do_install_wsl2, daemon=True).start()

    def _do_install_wsl2(self):
        if platform.system() == "Windows":
            from platforms.windows import wsl2_installer
            success = wsl2_installer.install_wsl(lambda m: print(f"[WSL2] {m}"))
            if success:
                self.after(0, lambda: self._update_status("wsl2", True, "✅ Installed"))
            else:
                self.after(0, lambda: self._update_status("wsl2", False, "❌ Failed"))

    def _update_status(self, key, passed, text):
        status_lbl = self.items[key]["status"]
        btn = self.items[key]["btn"]
        if passed:
            status_lbl.configure(text=text, text_color=SUCCESS_COLOR)
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

        # 2. Disk Space Check (20GB)
        disk_ok = False
        try:
            total, used, free = shutil.disk_usage("/")
            disk_ok = (free / (1024**3)) >= 20.0
        except Exception:
            disk_ok = True # Fallback if check fails

        results = {
            "docker": system_check.check_docker(),
            "python": system_check.check_python(),
            "git": system_check.check_git(),
            "ram": system_check.get_ram_info()["total_gb"] >= 8.0,
            "disk": disk_ok,
            "internet": internet
        }
        if platform.system() == "Windows":
            results["wsl2"] = system_check.check_wsl2()

        for key, passed in results.items():
            self.after(0, lambda k=key, p=passed: self._update_status(k, p, "✅ Found" if p else "❌ Missing"))
