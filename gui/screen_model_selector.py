import customtkinter as ctk
import threading
import os
from gui.theme import *
from utils import ollama_manager

MODELS = [
    {"id": "llama3.2:3b", "desc": "Fastest, low RAM (4GB)", "tag": "General"},
    {"id": "llama3.2:8b", "desc": "Balanced (8GB RAM)", "tag": "General"},
    {"id": "mistral:7b", "desc": "Great for coding (8GB RAM)", "tag": "Coding"},
    {"id": "deepseek-coder-v2:16b", "desc": "Best for code (16GB RAM)", "tag": "Coding"},
    {"id": "codellama:13b", "desc": "Meta's code specialist (12GB RAM)", "tag": "Coding"},
    {"id": "phi3:mini", "desc": "Tiny but smart (4GB RAM)", "tag": "General"},
    {"id": "gemma2:9b", "desc": "Google model (10GB RAM)", "tag": "General"},
    {"id": "qwen2.5-coder:7b", "desc": "Alibaba code model (8GB RAM)", "tag": "Coding"},
    {"id": "llama3.1:70b", "desc": "Most powerful (48GB RAM, slow)", "tag": "Heavy"},
    {"id": "nomic-embed-text", "desc": "Embeddings only, required for memory", "tag": "Required"}
]

class ScreenModelSelector(ctk.CTkFrame):
    def __init__(self, master, on_next, on_prev, **kwargs):
        super().__init__(master, fg_color=BG_COLOR, **kwargs)
        self.on_next = on_next
        self.on_prev = on_prev
        self.selected_models = set(["nomic-embed-text"])

        self.title = ctk.CTkLabel(self, text="Select Local LLM Models", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.status_lbl = ctk.CTkLabel(self, text="Checking Ollama installation...", font=FONT_MAIN, text_color=MUTED_TEXT)
        self.status_lbl.pack(pady=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_BG, width=600, height=300)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_pull = ctk.CTkButton(self, text="Pull Selected Models", command=self.pull_models, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        self.btn_pull.pack(pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=self.on_prev, fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, state="disabled", fg_color=PANEL_BG)
        self.btn_next.pack(side="left", padx=10)

        self.after(500, self.check_ollama)

    def handle_next(self):
        self.on_next({"models": list(self.selected_models)})

    def check_ollama(self):
        installed = ollama_manager.is_ollama_installed()
        if not installed:
            self.status_lbl.configure(text="Ollama not found. It will be installed automatically.", text_color=ERROR_COLOR)
        else:
            self.status_lbl.configure(text="Ollama detected.", text_color=SUCCESS_COLOR)
        self.populate_models()

    def populate_models(self):
        for m in MODELS:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR, border_width=1, border_color=MUTED_TEXT)
            card.pack(fill="x", pady=5, padx=5)

            var = ctk.BooleanVar(value=(m["id"] in self.selected_models))
            
            def toggle(model_id=m["id"], v=var):
                if model_id == "nomic-embed-text":
                    v.set(True) # Force true
                elif v.get():
                    self.selected_models.add(model_id)
                else:
                    self.selected_models.discard(model_id)

            cb = ctk.CTkCheckBox(
                card, text=f"{m['id']} - {m['desc']}", variable=var, command=toggle,
                font=FONT_MAIN, text_color=TEXT_COLOR, fg_color=ACCENT_COLOR
            )
            cb.pack(side="left", padx=10, pady=10)

            tag = ctk.CTkLabel(card, text=f" {m['tag']} ", fg_color=PANEL_BG, text_color=ACCENT_COLOR, corner_radius=5)
            tag.pack(side="right", padx=10)

    def pull_models(self):
        self.btn_pull.configure(state="disabled", text="Pulling...")
        threading.Thread(target=self._do_pull, daemon=True).start()

    def _do_pull(self):
        installed = ollama_manager.is_ollama_installed()
        if not installed:
            self.status_lbl.configure(text="Installing Ollama...", text_color=ACCENT_COLOR)
            def log_install(msg):
                self.status_lbl.configure(text=f"Installing Ollama: {msg[:50]}...", text_color=ACCENT_COLOR)
            try:
                from platforms.common.ollama_universal import setup_ollama
                from pathlib import Path
                import platform
                if platform.system() == "Windows":
                    install_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "Ollama"
                else:
                    install_dir = Path.home() / ".ollama_bin"
                install_dir.mkdir(parents=True, exist_ok=True)
                success = setup_ollama(install_dir, log_install)
                if not success:
                    self.status_lbl.configure(text="Failed to install Ollama.", text_color=ERROR_COLOR)
                    self.btn_pull.configure(state="normal", text="Retry")
                    return
            except Exception as e:
                self.status_lbl.configure(text=f"Error installing Ollama: {e}", text_color=ERROR_COLOR)
                self.btn_pull.configure(state="normal", text="Retry")
                return

        for model in self.selected_models:
            self.status_lbl.configure(text=f"Pulling {model}...", text_color=ACCENT_COLOR)
            def log_cb(msg):
                # Update status label with the latest log message
                self.status_lbl.configure(text=f"Pulling {model}: {msg[:50]}...", text_color=ACCENT_COLOR)
            success = ollama_manager.pull_model(model, log_cb)
            if not success:
                self.status_lbl.configure(text=f"Failed to pull {model}.", text_color=ERROR_COLOR)
                self.btn_pull.configure(state="normal", text="Retry")
                return
        
        self.status_lbl.configure(text="All selected models pulled successfully.", text_color=SUCCESS_COLOR)
        self.btn_pull.configure(text="Done", fg_color=SUCCESS_COLOR)
        self.btn_next.configure(state="normal", fg_color=ACCENT_COLOR, text_color=BG_COLOR)
