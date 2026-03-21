import sys
import argparse
import time
import json
import threading
import subprocess
import os
from pathlib import Path
import customtkinter as ctk

# Setup global error handling
from utils.error_handler import setup_error_handler
setup_error_handler()

import config
from utils.updater import check_for_updates, show_update_banner
from gui.theme import set_theme

# Import all screens
from gui.screen_welcome import WelcomeScreen
from gui.screen_requirements import RequirementsScreen
from gui.screen_drive_selector import DriveSelectorScreen
from gui.screen_port_selector import PortSelectorScreen
from gui.screen_model_selector import ModelSelectorScreen
from gui.screen_agent_selector import AgentSelectorScreen
from gui.screen_api_key import APIKeyScreen
from gui.screen_telegram import TelegramScreen
from gui.screen_install import InstallScreen
from gui.screen_manage import ManageScreen


# Imported config above already

class ClawSetupApp(ctk.CTk):
    def __init__(self, repair_mode=False, uninstall_mode=False):
        super().__init__()
        
        self.title("ClawSetup - OpenClaw Installer")
        self.geometry("800x600")
        self.resizable(False, False)
        
        set_theme()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 800) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")

        self.install_data = {}
        self.is_installed = False
        
        # Show splash screen first
        self.show_splash()

    def show_splash(self):
        # Clear everything
        for widget in self.winfo_children():
            widget.destroy()
            
        self.splash_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.splash_frame.pack(fill="both", expand=True)
        
        logo = ctk.CTkLabel(self.splash_frame, text="/// CLAW SETUP ///", font=("JetBrains Mono", 36, "bold"), text_color="#00F5FF")
        logo.pack(expand=True)
        
        self.progress = ctk.CTkProgressBar(self.splash_frame, width=400, height=10, progress_color="#00F5FF")
        self.progress.pack(pady=40)
        self.progress.set(0)
        
        def animate(val):
            if val <= 1.0:
                self.progress.set(val)
                self.after(30, animate, val + 0.05)
            else:
                self.show_main_content()
                
        self.after(100, animate, 0)

    def show_main_content(self):
        try:
            # Clear everything
            for widget in self.winfo_children():
                widget.destroy()
            
            # Re-check install state fresh from disk
            self.is_installed = config.INSTALL_STATE_FILE.exists()
            if self.is_installed:
                self.load_install_data()
            
            # Build main layout
            self.setup_main_layout()
            
            # Route to correct screen
            if self.is_installed:
                self.load_screen("manage")
            else:
                self.load_screen("welcome")
                
        except Exception as e:
            # Show error visibly instead of blank window
            import traceback
            error_label = ctk.CTkLabel(
                self, 
                text=f"Startup Error:\n{traceback.format_exc()}",
                text_color="red",
                wraplength=600,
                justify="left"
            )
            error_label.pack(padx=20, pady=20)

    def setup_main_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0A0F16")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        sidebar_title = ctk.CTkLabel(self.sidebar, text="INSTALLER", font=("JetBrains Mono", 16, "bold"), text_color="#00F5FF")
        sidebar_title.pack(pady=20)
        
        # Main content frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0D1117")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def load_screen(self, screen_name):
        try:
            # Clear main frame
            for widget in self.main_frame.winfo_children():
                widget.destroy()
            
            # Map screen names to classes
            screens = {
                "welcome": lambda: WelcomeScreen(self.main_frame, self),
                "requirements": lambda: RequirementsScreen(self.main_frame, self),
                "drive": lambda: DriveSelectorScreen(self.main_frame, self),
                "port": lambda: PortSelectorScreen(self.main_frame, self),
                "model": lambda: ModelSelectorScreen(self.main_frame, self),
                "agent": lambda: AgentSelectorScreen(self.main_frame, self),
                "api_key": lambda: APIKeyScreen(self.main_frame, self),
                "telegram": lambda: TelegramScreen(self.main_frame, self),
                "install": lambda: InstallScreen(self.main_frame, self),
                "manage": lambda: ManageScreen(self.main_frame, self),
            }
            
            if screen_name not in screens:
                raise ValueError(f"Unknown screen: {screen_name}")
                
            screen = screens[screen_name]()
            screen.grid(row=0, column=0, sticky="nsew")
            
        except Exception as e:
            import traceback
            error_label = ctk.CTkLabel(
                self.main_frame,
                text=f"Screen Load Error ({screen_name}):\n{traceback.format_exc()}",
                text_color="red",
                wraplength=500,
                justify="left"
            )
            error_label.grid(row=0, column=0, padx=20, pady=20)

    def load_install_data(self):
        if config.INSTALL_STATE_FILE.exists():
            try:
                with open(config.INSTALL_STATE_FILE, "r") as f:
                    self.install_data = json.load(f)
            except Exception as e:
                print(f"Failed to load install data: {e}")

    def do_uninstall(self):
        install_dir = self.install_data.get("install_dir")
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Uninstalling")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(dialog, text="Uninstalling OpenClaw...", font=("Roboto", 14))
        lbl.pack(pady=40)
        
        def run_cleanup():
            if install_dir and Path(install_dir).exists():
                try: subprocess.run(["docker", "compose", "down"], cwd=install_dir, capture_output=True, timeout=20)
                except Exception: pass
            
            if config.INSTALL_STATE_FILE.exists():
                try: os.remove(str(config.INSTALL_STATE_FILE))
                except Exception: pass
            
            self.after(1000, lambda: finish(dialog))

        def finish(win):
            win.destroy()
            self.load_screen("welcome")
            
        threading.Thread(target=run_cleanup, daemon=True).start()

def main():
    app = ClawSetupApp()
    app.mainloop()

if __name__ == "__main__":
    main()
