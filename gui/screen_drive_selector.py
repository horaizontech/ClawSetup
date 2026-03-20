import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from gui.theme import *
from utils import drive_selector

class ScreenDriveSelector(ctk.CTkFrame):
    def __init__(self, master, on_next, on_prev, **kwargs):
        super().__init__(master, fg_color=BG_COLOR, **kwargs)
        self.on_next = on_next
        self.on_prev = on_prev
        self.selected_path = None

        self.title = ctk.CTkLabel(self, text="Select Installation Directory", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.drives_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_BG, height=200)
        self.drives_frame.pack(pady=10, padx=20, fill="x")

        self.populate_drives()

        self.path_lbl = ctk.CTkLabel(self, text="Install Path:", font=FONT_MAIN, text_color=MUTED_TEXT)
        self.path_lbl.pack(pady=(20, 0))

        self.path_var = ctk.StringVar(value="Not selected")
        self.path_display = ctk.CTkEntry(self, textvariable=self.path_var, width=400, state="readonly", fg_color=BG_COLOR)
        self.path_display.pack(pady=5)

        self.btn_browse = ctk.CTkButton(self, text="Browse...", command=self.browse_folder, fg_color=PANEL_BG, border_width=1, border_color=ACCENT_COLOR)
        self.btn_browse.pack(pady=10)

        self.warning_lbl = ctk.CTkLabel(self, text="", font=FONT_MAIN, text_color=ERROR_COLOR)
        self.warning_lbl.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=self.on_prev, fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, state="disabled", fg_color=PANEL_BG)
        self.btn_next.pack(side="left", padx=10)

    def handle_next(self):
        if self.selected_path:
            self.on_next({"install_dir": str(self.selected_path)})
        else:
            self.on_next()

    def populate_drives(self):
        drives = drive_selector.get_mounted_drives()
        if not drives:
            ctk.CTkLabel(self.drives_frame, text="No drives found.", text_color=ERROR_COLOR).pack()
            return

        best_drive = max(drives, key=lambda d: d["free_gb"])

        for d in drives:
            card = ctk.CTkFrame(self.drives_frame, fg_color=BG_COLOR, border_width=1, border_color=MUTED_TEXT)
            card.pack(fill="x", pady=5, padx=5)
            
            text = f"Drive {d['mountpoint']} ({d['fstype']}) - {d['free_gb']}GB free of {d['total_gb']}GB"
            lbl = ctk.CTkLabel(card, text=text, font=FONT_MAIN, text_color=TEXT_COLOR)
            lbl.pack(side="left", padx=10, pady=10)

            if d == best_drive:
                badge = ctk.CTkLabel(card, text=" Recommended ", fg_color=SUCCESS_COLOR, text_color=BG_COLOR, corner_radius=5)
                badge.pack(side="right", padx=10)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Install Directory")
        if folder:
            path = Path(folder)
            self.selected_path = path / "OpenClaw"
            self.path_var.set(str(self.selected_path))
            
            # Check free space (simplified)
            try:
                import shutil
                free_gb = shutil.disk_usage(folder).free / (1024**3)
                if free_gb < 15:
                    self.warning_lbl.configure(text=f"Warning: Only {free_gb:.1f}GB free. 15GB+ recommended.")
                else:
                    self.warning_lbl.configure(text="")
                self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
            except Exception:
                pass
