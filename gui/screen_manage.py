import customtkinter as ctk
import webbrowser
from pathlib import Path
import json
from gui.theme import *
from config import INSTALL_STATE_FILE

class ManageScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        lbl_title = ctk.CTkLabel(self, text="Manage OpenHands Installation", font=("Roboto", 24, "bold"), text_color="#00F5FF")
        lbl_title.pack(pady=(40, 10))
        
        install_dir = self.app.install_data.get("install_dir", "Unknown")
        lbl_info = ctk.CTkLabel(self, text=f"OpenHands is currently installed at:\n{install_dir}", font=("Roboto", 14))
        lbl_info.pack(pady=(0, 30))
        
        btn_launch = ctk.CTkButton(self, text="Launch Dashboard", command=self.launch_dashboard, height=40, font=("Roboto", 14), fg_color=SUCCESS_COLOR, text_color=BG_COLOR)
        btn_launch.pack(pady=10, fill="x", padx=100)
        
        btn_repair = ctk.CTkButton(self, text="Repair Installation", command=lambda: self.app.load_screen("install"), height=40, font=("Roboto", 14))
        btn_repair.pack(pady=10, fill="x", padx=100)
        
        btn_uninstall = ctk.CTkButton(self, text="Uninstall OpenHands", command=self.handle_uninstall, height=40, font=("Roboto", 14), fg_color="#FF4444", hover_color="#CC0000")
        btn_uninstall.pack(pady=10, fill="x", padx=100)
        
        btn_exit = ctk.CTkButton(self, text="Exit", command=self.app.destroy, height=40, font=("Roboto", 14), fg_color="#333333", hover_color="#555555")
        btn_exit.pack(pady=10, fill="x", padx=100)

    def launch_dashboard(self):
        port = 3000
        if INSTALL_STATE_FILE.exists():
            try:
                state = json.loads(INSTALL_STATE_FILE.read_text())
                port = state.get("port", 3000)
            except Exception: pass
        
        url = f"http://localhost:{port}"
        webbrowser.open(url)

    def handle_uninstall(self):
        self.app.do_uninstall()
