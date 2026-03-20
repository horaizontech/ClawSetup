import customtkinter as ctk
from gui.theme import *
from utils.system_check import get_os_info

class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # ASCII Art Logo
        self.logo_label = ctk.CTkLabel(
            self, 
            text="""
   /\\   /\\   /\\
  /  \\ /  \\ /  \\
  |    |    |    |
   \\  / \\  / \\  /
    \\/   \\/   \\/
  OPENCLAW SETUP
            """, 
            font=FONT_MONO, 
            text_color=ACCENT_COLOR,
            justify="center"
        )
        self.logo_label.pack(pady=(40, 20))

        self.title = ctk.CTkLabel(self, text="Welcome to ClawSetup — OpenClaw Installer v1.0", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=10)

        desc_text = (
            "OpenClaw is your powerful, locally-hosted AI coding agent.\n"
            "It builds, debugs, and deploys code autonomously.\n"
            "This wizard will configure your environment and install all dependencies."
        )
        self.desc = ctk.CTkLabel(self, text=desc_text, font=FONT_MAIN, text_color=MUTED_TEXT, justify="center")
        self.desc.pack(pady=20)

        os_info = get_os_info()
        os_text = f"Detected System: {os_info['system']} {os_info['release']} ({os_info['architecture']})"
        self.os_label = ctk.CTkLabel(self, text=os_text, font=FONT_MAIN, text_color=SUCCESS_COLOR)
        self.os_label.pack(pady=20)

        self.btn_next = ctk.CTkButton(
            self, 
            text="Begin Setup", 
            command=lambda: self.app.load_screen("requirements"),
            fg_color=ACCENT_COLOR,
            text_color=BG_COLOR,
            hover_color="#00C4CC",
            font=("Roboto", 16, "bold"),
            height=40,
            width=200
        )
        self.btn_next.pack(pady=40)
