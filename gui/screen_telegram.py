import customtkinter as ctk
import webbrowser
from gui.theme import *

class TelegramScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        self.title = ctk.CTkLabel(self, text="Telegram Notifications", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.enable_var = ctk.BooleanVar(value=False)
        self.switch = ctk.CTkSwitch(
            self, text="Enable Telegram Notifications", variable=self.enable_var, command=self.toggle_fields,
            font=FONT_MAIN, text_color=TEXT_COLOR, progress_color=ACCENT_COLOR
        )
        self.switch.pack(pady=20)

        self.form_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, width=500)
        self.form_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.form_frame, text="Bot Token:", font=FONT_MAIN, text_color=TEXT_COLOR).pack(anchor="w", padx=20, pady=(10, 0))
        self.token_entry = ctk.CTkEntry(self.form_frame, show="*", width=400, state="disabled")
        self.token_entry.pack(padx=20, pady=5)
        
        link1 = ctk.CTkLabel(self.form_frame, text="How to get this (BotFather)", font=("Roboto", 12, "underline"), text_color=ACCENT_COLOR, cursor="hand2")
        link1.pack(anchor="w", padx=20)
        link1.bind("<Button-1>", lambda e: webbrowser.open("https://core.telegram.org/bots/features#botfather"))

        ctk.CTkLabel(self.form_frame, text="Chat ID:", font=FONT_MAIN, text_color=TEXT_COLOR).pack(anchor="w", padx=20, pady=(10, 0))
        self.chat_entry = ctk.CTkEntry(self.form_frame, width=400, state="disabled")
        self.chat_entry.pack(padx=20, pady=5)

        self.btn_test = ctk.CTkButton(self.form_frame, text="Test Connection", state="disabled", fg_color=PANEL_BG, border_width=1, border_color=MUTED_TEXT, command=self.test_connection)
        self.btn_test.pack(pady=15)

        self.options_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.options_frame.pack(pady=10, fill="x", padx=20)
        
        opts = ["Task Started", "Task Completed", "Task Failed", "Agent Switched", "New File Created"]
        self.cb_vars = []
        for opt in opts:
            var = ctk.BooleanVar(value=True)
            self.cb_vars.append(var)
            cb = ctk.CTkCheckBox(self.options_frame, text=opt, variable=var, state="disabled", font=FONT_MAIN, text_color=MUTED_TEXT, fg_color=ACCENT_COLOR)
            cb.pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=lambda: self.app.load_screen("agent"), fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        self.btn_next.pack(side="left", padx=10)

    def handle_next(self):
        token = self.token_entry.get() if self.enable_var.get() else ""
        chat_id = self.chat_entry.get() if self.enable_var.get() else ""
        self.app.install_data.update({
            "telegram_enabled": self.enable_var.get(),
            "telegram_token": token,
            "telegram_chat_id": chat_id
        })
        self.app.load_screen("install")

    def test_connection(self):
        token = self.token_entry.get().strip()
        chat_id = self.chat_entry.get().strip()
        if not token or not chat_id: return
        self.btn_test.configure(state="disabled", text="Testing...")
        def _test():
            import requests
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": "🤖 *OpenClaw Telegram Notifier* is online.", "parse_mode": "Markdown"}
            try:
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200: self.btn_test.configure(text="✅ Success", fg_color=SUCCESS_COLOR)
                else: self.btn_test.configure(text="❌ Failed", fg_color=ERROR_COLOR)
            except Exception: self.btn_test.configure(text="❌ Failed", fg_color=ERROR_COLOR)
            self.after(3000, lambda: self.btn_test.configure(state="normal", text="Test Connection", fg_color=ACCENT_COLOR))
        import threading
        threading.Thread(target=_test, daemon=True).start()

    def toggle_fields(self):
        state = "normal" if self.enable_var.get() else "disabled"
        self.token_entry.configure(state=state)
        self.chat_entry.configure(state=state)
        self.btn_test.configure(state=state, fg_color=ACCENT_COLOR if state=="normal" else PANEL_BG)
        for child in self.options_frame.winfo_children():
            if isinstance(child, ctk.CTkCheckBox): child.configure(state=state, text_color=TEXT_COLOR if state=="normal" else MUTED_TEXT)
