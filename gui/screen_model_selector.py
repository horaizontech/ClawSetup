import customtkinter as ctk
import threading
import os
import subprocess
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

class ModelSelectorScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.selected_models = set(["nomic-embed-text"])
        self.installed_models = []

        self.title = ctk.CTkLabel(self, text="Select Local LLM Models", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 5))

        # Status indicator below title
        self.status_lbl = ctk.CTkLabel(self, text="Checking Ollama status...", font=FONT_MAIN, text_color=MUTED_TEXT)
        self.status_lbl.pack(pady=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_BG, width=600, height=300)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_pull = ctk.CTkButton(self, text="Pull Selected Models", command=self.pull_models, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        self.btn_pull.pack(pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.btn_prev = ctk.CTkButton(btn_frame, text="Back", command=lambda: self.app.load_screen("port"), fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(btn_frame, text="Next", command=self.handle_next, fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        self.btn_next.pack(side="left", padx=10)

        # Run checks on load
        self.update_ollama_status()
        self.populate_models()

    def check_installed_models(self):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # skip header
                installed = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]  # first column is model name
                        # Standardize name (remove :latest if present for matching)
                        installed.append(model_name)
                return installed
            return []
        except FileNotFoundError:
            return None  # Special case for "not installed"
        except subprocess.TimeoutExpired:
            return []  # ollama not responding
        except Exception:
            return []

    def update_ollama_status(self):
        self.installed_models = self.check_installed_models()
        
        if self.installed_models is None:
            self.status_lbl.configure(text="● Ollama not detected — will be installed automatically", text_color="#EBCB8B")
            self.installed_models = []
        elif not self.installed_models and ollama_manager.is_ollama_installed():
            # Check if it's literally empty or just unresponsive
            try:
                subprocess.run(["ollama", "--version"], capture_output=True, timeout=2)
                self.status_lbl.configure(text="● Ollama running — 0 models already installed", text_color=SUCCESS_COLOR)
            except Exception:
                self.status_lbl.configure(text="● Ollama installed but not running — will start automatically", text_color="#EBCB8B")
        else:
            self.status_lbl.configure(
                text=f"● Ollama running — {len(self.installed_models)} models already installed", 
                text_color=SUCCESS_COLOR
            )

    def handle_next(self):
        self.app.install_data["models"] = list(self.selected_models)
        self.app.load_screen("agent")

    def populate_models(self):
        for m in MODELS:
            model_id = m["id"]
            is_installed = any(model_id in inst for inst in self.installed_models)
            
            card = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR, border_width=1, border_color=MUTED_TEXT)
            card.pack(fill="x", pady=5, padx=5)
            
            # Use BooleanVar for checkbox state
            initial_val = (model_id == "nomic-embed-text" or is_installed)
            if initial_val:
                self.selected_models.add(model_id)
                
            var = ctk.BooleanVar(value=initial_val)
            
            def toggle(mid=model_id, v=var):
                if mid == "nomic-embed-text":
                    v.set(True) # Stay required
                elif v.get():
                    self.selected_models.add(mid)
                else:
                    self.selected_models.discard(mid)

            cb = ctk.CTkCheckBox(
                card, text=f"{model_id} - {m['desc']}", variable=var, command=toggle, 
                font=FONT_MAIN, text_color=TEXT_COLOR, fg_color=ACCENT_COLOR
            )
            cb.pack(side="left", padx=10, pady=10)
            
            # Logic for tag and locking
            current_tag = m["tag"]
            tag_color = ACCENT_COLOR
            
            if model_id == "nomic-embed-text":
                current_tag = "Required ✓"
                tag_color = SUCCESS_COLOR
                cb.configure(state="disabled") # Locked
            elif is_installed:
                current_tag = "Installed ✓"
                tag_color = SUCCESS_COLOR
            
            tag = ctk.CTkLabel(card, text=f" {current_tag} ", fg_color=PANEL_BG, text_color=tag_color, corner_radius=5)
            tag.pack(side="right", padx=10)

    def pull_models(self):
        self.btn_pull.configure(state="disabled", text="Pulling...")
        threading.Thread(target=self._do_pull, daemon=True).start()

    def _do_pull(self):
        # 1. Ensure Ollama is installed
        if not ollama_manager.is_ollama_installed():
            self.status_lbl.configure(text="Installing Ollama...", text_color=ACCENT_COLOR)
            try:
                from platforms.common.ollama_universal import setup_ollama
                from pathlib import Path
                import platform
                if platform.system() == "Windows": 
                    install_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "Ollama"
                else: 
                    install_dir = Path.home() / ".ollama_bin"
                install_dir.mkdir(parents=True, exist_ok=True)
                
                def log_install(msg): self.after(0, lambda: self.status_lbl.configure(text=f"Ollama: {msg[:40]}..."))
                
                success = setup_ollama(install_dir, log_install)
                if not success:
                    self.after(0, lambda: self.status_lbl.configure(text="● Failed to install Ollama", text_color=ERROR_COLOR))
                    self.btn_pull.configure(state="normal", text="Retry")
                    return
            except Exception as e:
                self.after(0, lambda: self.status_lbl.configure(text=f"● Error install: {str(e)[:40]}", text_color=ERROR_COLOR))
                self.btn_pull.configure(state="normal", text="Retry")
                return

        # 2. Pull models (skip nomic-embed-text as it's handled in install screen or simply not here)
        models_to_pull = [m for m in self.selected_models if m != "nomic-embed-text"]
        
        if not models_to_pull:
            self.after(0, lambda: self.status_lbl.configure(text="● Ready to install (Nomic handled later)", text_color=SUCCESS_COLOR))
            self.btn_pull.configure(text="Done", state="normal")
            return

        for model in models_to_pull:
            # Skip if already installed
            if any(model in inst for inst in self.installed_models):
                continue
                
            self.after(0, lambda m=model: self.status_lbl.configure(text=f"● Pulling {m}...", text_color=ACCENT_COLOR))
            def log_cb(msg): 
                self.after(0, lambda m=msg: self.status_lbl.configure(text=f"● {model}: {m[:40]}..."))
            
            success = ollama_manager.pull_model(model, log_cb)
            if not success:
                self.after(0, lambda m=model: self.status_lbl.configure(text=f"● Failed {m}", text_color=ERROR_COLOR))
                self.btn_pull.configure(state="normal", text="Retry")
                return
        
        self.after(0, self.update_and_finish)

    def update_and_finish(self):
        self.update_ollama_status()
        self.status_lbl.configure(text="● All selected models pulled successfully.", text_color=SUCCESS_COLOR)
        self.btn_pull.configure(text="Done", fg_color=SUCCESS_COLOR, state="normal")
        
        # Refresh the screen to show "Installed" labels
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.populate_models()
