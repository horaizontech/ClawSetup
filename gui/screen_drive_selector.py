import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from gui.theme import *
from utils import drive_selector

class DriveSelectorScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.selected_path = None
        self.selected_drive = None
        self.drive_cards = []

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

        self.warning_lbl = ctk.CTkLabel(self, text="", font=FONT_MAIN)
        self.warning_lbl.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=lambda: self.app.load_screen("requirements"), fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, state="disabled", fg_color=PANEL_BG)
        self.btn_next.pack(side="left", padx=10)

    def handle_next(self):
        if not self.selected_path:
            return

        # Double check space for 15GB warning
        try:
            import shutil
            free_gb = shutil.disk_usage(self.selected_path.anchor).free / (1024**3)
            if free_gb < 15.0:
                if not messagebox.askyesno("Storage Warning", 
                    f"This drive has only {free_gb:.1f}GB free. OpenClaw may not run properly. Continue anyway?"):
                    return
        except Exception:
            pass

        self.app.install_data["install_dir"] = str(self.selected_path)
        self.app.load_screen("port")

    def populate_drives(self):
        drives = drive_selector.get_mounted_drives()
        if not drives:
            ctk.CTkLabel(self.drives_frame, text="No drives found.", text_color=ERROR_COLOR).pack()
            return

        best_drive = max(drives, key=lambda d: d["free_gb"])

        for d in drives:
            card = ctk.CTkFrame(self.drives_frame, fg_color=BG_COLOR, border_width=1, border_color=MUTED_TEXT, cursor="hand2")
            card.pack(fill="x", pady=5, padx=5)
            
            text = f"Drive {d['mountpoint']} ({d['fstype']}) - {d['free_gb']}GB free of {d['total_gb']}GB"
            lbl = ctk.CTkLabel(card, text=text, font=FONT_MAIN, text_color=TEXT_COLOR)
            lbl.pack(side="left", padx=10, pady=10)

            if d == best_drive:
                badge = ctk.CTkLabel(card, text=" Recommended ", fg_color=SUCCESS_COLOR, text_color=BG_COLOR, corner_radius=5)
                badge.pack(side="right", padx=10)

            for widget in [card, lbl]:
                widget.bind("<Button-1>", lambda e, d=d, c=card: self.select_drive(d, c))
            if d == best_drive:
                for widget in card.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        widget.bind("<Button-1>", lambda e, d=d, c=card: self.select_drive(d, c))

            self.drive_cards.append((card, d))

        self.select_drive(best_drive, self.drive_cards[0][0])

    def select_drive(self, drive_info, card_widget):
        self.selected_drive = drive_info
        for card, info in self.drive_cards:
            if card == card_widget:
                card.configure(border_color=ACCENT_COLOR, border_width=2)
            else:
                card.configure(border_color=MUTED_TEXT, border_width=1)
        self.selected_path = Path(drive_info["mountpoint"]) / "OpenClaw"
        self.path_var.set(str(self.selected_path))
        self.validate_space(drive_info["free_gb"])

    def validate_space(self, free_gb):
        if free_gb < 2.0:
            self.warning_lbl.configure(text=f"❌ Error: Only {free_gb:.1f}GB free. 2GB required.", text_color=ERROR_COLOR)
            self.btn_next.configure(state="disabled", fg_color=PANEL_BG)
        elif free_gb < 15.0:
            self.warning_lbl.configure(text=f"⚠️ Warning: Only {free_gb:.1f}GB free. 15GB recommended.", text_color="#EBCB8B")
            self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        else:
            self.warning_lbl.configure(text="✅ Storage sufficient", text_color=SUCCESS_COLOR)
            self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)

    def browse_folder(self):
        initial_dir = self.selected_drive["mountpoint"] if self.selected_drive else None
        folder = filedialog.askdirectory(title="Select Install Directory", initialdir=initial_dir)
        if folder:
            path = Path(folder)
            self.selected_path = path / "OpenClaw"
            self.path_var.set(str(self.selected_path))
            try:
                import shutil
                usage = shutil.disk_usage(folder)
                self.validate_space(usage.free / (1024**3))
            except Exception:
                pass
