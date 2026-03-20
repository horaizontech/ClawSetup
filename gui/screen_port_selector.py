import customtkinter as ctk
import threading
from gui.theme import *
from utils import port_scanner

class PortSelectorScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.selected_port = ctk.IntVar(value=18789)

        self.title = ctk.CTkLabel(self, text="Network Configuration", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        desc = "OpenClaw runs a local dashboard. Select an available port for it."
        self.desc_lbl = ctk.CTkLabel(self, text=desc, font=FONT_MAIN, text_color=MUTED_TEXT)
        self.desc_lbl.pack(pady=10)

        self.ports_frame = ctk.CTkFrame(self, fg_color=PANEL_BG)
        self.ports_frame.pack(pady=20, padx=20, fill="x")

        self.loading_lbl = ctk.CTkLabel(self.ports_frame, text="Scanning ports...", font=FONT_MAIN, text_color=ACCENT_COLOR)
        self.loading_lbl.pack(pady=20)

        self.custom_port_var = ctk.StringVar()
        self.custom_entry = ctk.CTkEntry(self, textvariable=self.custom_port_var, placeholder_text="Advanced: Enter custom port", width=250)
        self.custom_entry.pack(pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=lambda: self.app.load_screen("drive"), fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, state="disabled", fg_color=PANEL_BG)
        self.btn_next.pack(side="left", padx=10)

        self.after(500, self.scan_ports)

    def handle_next(self):
        port = self.custom_port_var.get()
        if not port:
            port = self.selected_port.get()
        self.app.install_data["port"] = int(port)
        self.app.load_screen("model")

    def scan_ports(self):
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        # Scan starting from 18789
        ports = port_scanner.get_available_ports(start_port=18789, end_port=19999, count=3)
        self.loading_lbl.destroy()
        if not ports:
            ctk.CTkLabel(self.ports_frame, text="No available ports found.", text_color=ERROR_COLOR).pack()
            return
        self.selected_port.set(ports[0])
        for p in ports:
            rb = ctk.CTkRadioButton(
                self.ports_frame, text=f"Port {p} (Available)", variable=self.selected_port, value=p,
                font=FONT_MAIN, text_color=TEXT_COLOR, fg_color=ACCENT_COLOR
            )
            rb.pack(pady=10, anchor="w", padx=20)
        self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
