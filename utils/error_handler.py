import sys
import traceback
import os
import platform
from pathlib import Path
import customtkinter as ctk

from gui.theme import *
from config import BASE_DIR

# Try importing the telegram notifier if available
try:
    from templates.telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None

def get_log_dir() -> Path:
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def log_error(exc_type, exc_value, exc_traceback):
    """Writes the full traceback to logs/error.log"""
    log_dir = get_log_dir()
    error_file = log_dir / "error.log"
    
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    with open(error_file, "a") as f:
        f.write(f"--- UNHANDLED EXCEPTION ---\n")
        f.write(tb_str)
        f.write("\n")
        
    return tb_str

def show_error_dialog(tb_str: str):
    """Shows a friendly error dialog using CustomTkinter."""
    dialog = ctk.CTkToplevel()
    dialog.title("ClawSetup - Unexpected Error")
    dialog.geometry("600x400")
    dialog.attributes("-topmost", True)
    dialog.grab_set()

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - 600) // 2
    y = (dialog.winfo_screenheight() - 400) // 2
    dialog.geometry(f"+{x}+{y}")

    lbl_title = ctk.CTkLabel(dialog, text="Oops! Something went wrong.", font=("Roboto", 18, "bold"), text_color="#FF4444")
    lbl_title.pack(pady=(20, 10))

    lbl_desc = ctk.CTkLabel(dialog, text="An unexpected error occurred. The details have been saved to logs/error.log.", font=("Roboto", 12))
    lbl_desc.pack(pady=(0, 10))

    textbox = ctk.CTkTextbox(dialog, width=550, height=200, font=("JetBrains Mono", 10))
    textbox.pack(pady=10)
    textbox.insert("0.0", tb_str)
    textbox.configure(state="disabled")

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=10)

    def copy_error():
        dialog.clipboard_clear()
        dialog.clipboard_append(tb_str)
        dialog.update()

    def open_log_folder():
        log_dir = get_log_dir().absolute()
        if platform.system() == "Windows":
            os.startfile(log_dir)
        elif platform.system() == "Darwin":
            os.system(f"open '{log_dir}'")
        else:
            os.system(f"xdg-open '{log_dir}'")

    btn_copy = ctk.CTkButton(btn_frame, text="Copy Error", command=copy_error, fg_color="#333333", hover_color="#555555")
    btn_copy.pack(side="left", padx=10)

    btn_open = ctk.CTkButton(btn_frame, text="Open Log Folder", command=open_log_folder, fg_color="#333333", hover_color="#555555")
    btn_open.pack(side="left", padx=10)

    btn_close = ctk.CTkButton(btn_frame, text="Close", command=dialog.destroy, fg_color="#FF4444", hover_color="#CC0000")
    btn_close.pack(side="left", padx=10)

    dialog.wait_window()

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """The global exception handler hooked into sys.excepthook."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_str = log_error(exc_type, exc_value, exc_traceback)
    
    # Try sending to Telegram if configured
    if TelegramNotifier:
        try:
            # We would need the env vars loaded, but assuming they are if the app got this far
            notifier = TelegramNotifier()
            if notifier.is_configured():
                msg = f"🚨 *ClawSetup Crash Report*\n\n```python\n{tb_str[:3000]}\n```"
                notifier.send_message(msg)
        except Exception:
            pass

    show_error_dialog(tb_str)

def setup_error_handler():
    """Call this function at the start of main.py to enable global error handling."""
    sys.excepthook = global_exception_handler
