import sys
import argparse
import time
import json
import threading
import subprocess
import os
from pathlib import Path
import customtkinter as ctk

# Setup global error handling first
from utils.error_handler import setup_error_handler
setup_error_handler()

from utils.updater import check_for_updates, show_update_banner
from gui.theme import set_theme

# Import all wizard screens
from gui.screen_welcome import ScreenWelcome
from gui.screen_requirements import ScreenRequirements
from gui.screen_drive_selector import ScreenDriveSelector
from gui.screen_port_selector import ScreenPortSelector
from gui.screen_model_selector import ScreenModelSelector
from gui.screen_agent_selector import ScreenAgentSelector
from gui.screen_telegram import ScreenTelegram
from gui.screen_install import ScreenInstall

# Centralized path for installation state
INSTALL_STATE_FILE = Path.home() / ".clawsetup_state.json"

class ScreenManage(ctk.CTkFrame):
    """Screen shown when ClawSetup is already installed."""
    def __init__(self, master, install_data, on_repair, on_uninstall, on_exit):
        super().__init__(master, fg_color="transparent")
        
        lbl_title = ctk.CTkLabel(self, text="ClawSetup Manager", font=("Roboto", 24, "bold"), text_color="#00F5FF")
        lbl_title.pack(pady=(40, 10))
        
        install_dir = install_data.get("install_dir", "Unknown")
        lbl_info = ctk.CTkLabel(self, text=f"OpenClaw is currently installed at:\n{install_dir}", font=("Roboto", 14))
        lbl_info.pack(pady=(0, 30))
        
        btn_repair = ctk.CTkButton(self, text="Repair Installation", command=on_repair, height=40, font=("Roboto", 14))
        btn_repair.pack(pady=10, fill="x", padx=100)
        
        btn_uninstall = ctk.CTkButton(self, text="Uninstall OpenClaw", command=on_uninstall, height=40, font=("Roboto", 14), fg_color="#FF4444", hover_color="#CC0000")
        btn_uninstall.pack(pady=10, fill="x", padx=100)
        
        btn_exit = ctk.CTkButton(self, text="Exit", command=on_exit, height=40, font=("Roboto", 14), fg_color="#333333", hover_color="#555555")
        btn_exit.pack(pady=10, fill="x", padx=100)

class ClawSetupApp(ctk.CTk):
    def __init__(self, repair_mode=False, uninstall_mode=False):
        super().__init__()
        
        self.title("ClawSetup - OpenClaw Installer")
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Initialize theme correctly
        set_theme()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 800) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")

        self.install_data = {}
        self.current_step = 0
        self.screens = []
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        # Check for updates in background
        check_for_updates(self.on_update_available)

        if uninstall_mode:
            self.load_install_data()
            self.do_uninstall()
            return
            
        if repair_mode:
            self.load_install_data()
            self.start_wizard()
            return

        # Show splash screen first
        self.show_splash()

    def clear_screen(self):
        """Safely clear all widgets from the main container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def load_install_data(self):
        """Force re-read installation state from disk."""
        if INSTALL_STATE_FILE.exists():
            try:
                with open(INSTALL_STATE_FILE, "r") as f:
                    self.install_data = json.load(f)
            except Exception as e:
                print(f"Failed to load install data: {e}")
                self.install_data = {}
        else:
            self.install_data = {}

    def on_update_available(self, new_version, release_url):
        self.after(0, lambda: show_update_banner(self, new_version, release_url))

    def show_splash(self):
        self.clear_screen()
        self.splash_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.splash_frame.pack(fill="both", expand=True)
        
        logo = ctk.CTkLabel(self.splash_frame, text="/// CLAW SETUP ///", font=("JetBrains Mono", 36, "bold"), text_color="#00F5FF")
        logo.pack(expand=True)
        
        self.progress = ctk.CTkProgressBar(self.splash_frame, width=400, height=10, progress_color="#00F5FF")
        self.progress.pack(pady=40)
        self.progress.set(0)
        
        def animate(val):
            if val <= 1.0:
                self.progress.set(val)
                self.after(30, animate, val + 0.02)
            else:
                self.splash_frame.destroy()
                self.check_install_state()
                
        self.after(100, animate, 0)

    def check_install_state(self):
        self.load_install_data()
        if self.install_data:
            self.show_manage_screen()
        else:
            self.start_wizard()

    def show_manage_screen(self):
        self.clear_screen()
        manage_screen = ScreenManage(
            self.container, 
            self.install_data,
            on_repair=self.start_wizard,
            on_uninstall=self.do_uninstall,
            on_exit=self.destroy
        )
        manage_screen.pack(fill="both", expand=True)

    def do_uninstall(self):
        install_dir = self.install_data.get("install_dir")
        
        msg = "Uninstalling OpenClaw...\nCompleting cleanup..."
        if install_dir:
            msg = f"Uninstalling OpenClaw from:\n{install_dir}\nStopping containers..."

        dialog = ctk.CTkToplevel(self)
        dialog.title("Uninstalling")
        dialog.geometry("500x300")
        dialog.attributes("-topmost", True)
        
        # Center dialog
        dx = self.winfo_x() + (800 - 500) // 2
        dy = self.winfo_y() + (600 - 300) // 2
        dialog.geometry(f"+{dx}+{dy}")
        
        lbl = ctk.CTkLabel(dialog, text=msg, font=("Roboto", 14), justify="center")
        lbl.pack(pady=40)
        
        def run_cleanup():
            # 1. Stop Docker
            if install_dir and Path(install_dir).exists():
                try:
                    subprocess.run(["docker", "compose", "down"], cwd=install_dir, capture_output=True, timeout=30)
                except Exception as e:
                    print(f"Docker cleanup warning: {e}")
            
            # 2. Force delete state file
            if INSTALL_STATE_FILE.exists():
                try:
                    INSTALL_STATE_FILE.unlink()
                except Exception:
                    try:
                        os.remove(str(INSTALL_STATE_FILE))
                    except Exception as e:
                        print(f"Critical: Failed to delete state file: {e}")
            
            # Verify deletion
            if INSTALL_STATE_FILE.exists():
                print("Warning: State file still exists after uninstall attempt.")
            
            self.after(500, lambda: finish(dialog))

        def finish(win):
            win.destroy()
            self.clear_screen()
            
            # Show success message
            success_lbl = ctk.CTkLabel(self.container, 
                text="✅ OpenClaw has been removed successfully.\nYou can reinstall it at any time.", 
                font=("Roboto", 18, "bold"), text_color="#2ECC71")
            success_lbl.pack(expand=True)
            
            # Reset internal state
            self.install_data = {}
            
            # Delay before reloading welcome screen
            self.after(2000, self.start_wizard)
            
        threading.Thread(target=run_cleanup, daemon=True).start()

    def start_wizard(self):
        self.clear_screen()
            
        self.screens = [
            ScreenWelcome(self.container, self.next_screen),
            ScreenRequirements(self.container, self.next_screen, self.prev_screen),
            ScreenDriveSelector(self.container, self.next_screen, self.prev_screen),
            ScreenPortSelector(self.container, self.next_screen, self.prev_screen),
            ScreenModelSelector(self.container, self.next_screen, self.prev_screen),
            ScreenAgentSelector(self.container, self.next_screen, self.prev_screen),
            ScreenTelegram(self.container, self.next_screen, self.prev_screen),
            ScreenInstall(self.container, self.finish_setup, self.prev_screen, self.install_data)
        ]
        
        self.current_step = 0
        self.show_current_screen()

    def show_current_screen(self):
        for i, screen in enumerate(self.screens):
            if i == self.current_step:
                screen.pack(fill="both", expand=True)
            else:
                screen.pack_forget()

    def next_screen(self, data=None):
        if data:
            self.install_data.update(data)
            
        if self.current_step < len(self.screens) - 1:
            self.current_step += 1
            self.show_current_screen()

    def prev_screen(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.show_current_screen()

    def finish_setup(self):
        try:
            with open(INSTALL_STATE_FILE, "w") as f:
                json.dump(self.install_data, f)
        except Exception as e:
            print(f"Failed to save install state: {e}")
            
        self.destroy()

def main():
    parser = argparse.ArgumentParser(description="ClawSetup - OpenClaw Installer")
    parser.add_argument("--repair", action="store_true", help="Force repair/reinstall mode")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall OpenClaw")
    args = parser.parse_args()

    app = ClawSetupApp(repair_mode=args.repair, uninstall_mode=args.uninstall)
    app.mainloop()

if __name__ == "__main__":
    main()
