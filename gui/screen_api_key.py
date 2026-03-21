import customtkinter as ctk
import webbrowser
from gui.theme import *

class APIKeyScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        self.title = ctk.CTkLabel(self, text="AI Provider Configuration", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 20))

        # Provider Selection
        self.provider_var = ctk.StringVar(value="anthropic")
        
        provider_frame = ctk.CTkFrame(self, fg_color=PANEL_BG)
        provider_frame.pack(pady=10, padx=40, fill="x")

        ctk.CTkLabel(provider_frame, text="Select AI Provider:", font=FONT_MAIN).pack(pady=(10, 5))

        self.radio_anthropic = ctk.CTkRadioButton(
            provider_frame, text="Anthropic Claude", variable=self.provider_var, value="anthropic", 
            command=self.on_provider_change, hover_color=ACCENT_COLOR, fg_color=ACCENT_COLOR
        )
        self.radio_anthropic.pack(pady=5, padx=20, anchor="w")

        self.radio_openai = ctk.CTkRadioButton(
            provider_frame, text="OpenAI", variable=self.provider_var, value="openai", 
            command=self.on_provider_change, hover_color=ACCENT_COLOR, fg_color=ACCENT_COLOR
        )
        self.radio_openai.pack(pady=5, padx=20, anchor="w")

        self.radio_ollama = ctk.CTkRadioButton(
            provider_frame, text="Ollama (Local AI)", variable=self.provider_var, value="ollama", 
            command=self.on_provider_change, hover_color=ACCENT_COLOR, fg_color=ACCENT_COLOR
        )
        self.radio_ollama.pack(pady=5, padx=20, anchor="w")

        # API Key Input
        self.key_frame = ctk.CTkFrame(self, fg_color=PANEL_BG)
        self.key_frame.pack(pady=20, padx=40, fill="x")

        self.lbl_key = ctk.CTkLabel(self.key_frame, text="API Key:", font=FONT_MAIN)
        self.lbl_key.pack(pady=(10, 5))

        self.entry_key = ctk.CTkEntry(self.key_frame, width=400, show="*", placeholder_text="sk-ant-...", font=FONT_MAIN)
        self.entry_key.pack(pady=5, padx=20)

        self.btn_link = ctk.CTkButton(
            self.key_frame, text="Get API Key", font=("Roboto", 10, "underline"), 
            fg_color="transparent", text_color=ACCENT_COLOR, hover=False, command=self.open_link
        )
        self.btn_link.pack(pady=(0, 10))

        # Ollama Message
        self.ollama_frame = ctk.CTkFrame(self, fg_color=PANEL_BG)
        self.lbl_ollama = ctk.CTkLabel(
            self.ollama_frame, 
            text="No API key needed — using local models via Ollama.\nMake sure Ollama is running!", 
            font=FONT_MAIN, text_color=SUCCESS_COLOR
        )
        self.lbl_ollama.pack(pady=20, padx=20)

        # Navigation
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_prev = ctk.CTkButton(
            btn_frame, text="Back", command=lambda: self.app.load_screen("agent_selector"),
            fg_color=PANEL_BG, text_color=TEXT_COLOR
        )
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            btn_frame, text="Next", command=self.handle_next,
            fg_color=ACCENT_COLOR, text_color=BG_COLOR
        )
        self.btn_next.pack(side="left", padx=10)

        self.on_provider_change()

    def on_provider_change(self):
        p = self.provider_var.get()
        if p == "ollama":
            self.key_frame.pack_forget()
            self.ollama_frame.pack(pady=20, padx=40, fill="x", after=self.title)
        else:
            self.ollama_frame.pack_forget()
            self.key_frame.pack(pady=20, padx=40, fill="x", after=self.title)
            if p == "anthropic":
                self.entry_key.configure(placeholder_text="sk-ant-...")
            else:
                self.entry_key.configure(placeholder_text="sk-proj-...")

    def open_link(self):
        p = self.provider_var.get()
        if p == "anthropic":
            webbrowser.open("https://console.anthropic.com/settings/keys")
        elif p == "openai":
            webbrowser.open("https://platform.openai.com/api-keys")

    def handle_next(self):
        provider = self.provider_var.get()
        key = self.entry_key.get().strip()

        if provider != "ollama":
            if not key:
                # Add a validation error UI here if needed
                return
            if provider == "anthropic" and not key.startswith("sk-ant-"):
                # Warning
                pass
            if provider == "openai" and not key.startswith("sk-"):
                # Warning
                pass

        self.app.ai_provider = provider
        self.app.api_key = key
        self.app.load_screen("telegram")
