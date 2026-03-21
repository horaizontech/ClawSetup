import customtkinter as ctk
from gui.theme import *

AGENTS = [
    {"name": "FullStack Dev", "icon": "🧑💻", "desc": "Builds complete web apps end-to-end", "tools": "React, Node, DB"},
    {"name": "Bug Hunter", "icon": "🐛", "desc": "Finds and fixes bugs across any codebase", "tools": "Debugger, Grep"},
    {"name": "DocWriter", "icon": "📝", "desc": "Generates READMEs, API docs, inline comments", "tools": "Markdown, Sphinx"},
    {"name": "SecAudit", "icon": "🔒", "desc": "Reviews code for security vulnerabilities", "tools": "SAST, Bandit"},
    {"name": "TestEngineer", "icon": "🧪", "desc": "Writes unit, integration, and e2e tests", "tools": "PyTest, Jest"},
    {"name": "DBArchitect", "icon": "🗄️", "desc": "Designs schemas, writes SQL, optimizes queries", "tools": "SQL, Prisma"},
    {"name": "AgentBuilder", "icon": "🤖", "desc": "Builds other AI agents and automation pipelines", "tools": "LangChain, Docker"},
    {"name": "DataAnalyst", "icon": "📊", "desc": "Analyzes data, writes pandas/numpy code, plots charts", "tools": "Pandas, Matplotlib"},
    {"name": "APIIntegrator", "icon": "🌐", "desc": "Connects APIs, writes webhook handlers, REST/GraphQL", "tools": "Requests, FastAPI"},
    {"name": "DevOps Engineer", "icon": "🚀", "desc": "Dockerfiles, CI/CD pipelines, cloud deployment scripts", "tools": "Docker, GitHub Actions"}
]

class AgentSelectorScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app
        self.selected_agents = set()
        self.vars = {}

        self.title = ctk.CTkLabel(self, text="Select Agent Profiles", font=FONT_HEADING, text_color=TEXT_COLOR)
        self.title.pack(pady=(20, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_BG, width=600, height=350)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.populate_agents()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Select All", command=self.select_all, width=100, fg_color=PANEL_BG).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Clear", command=self.clear_all, width=100, fg_color=PANEL_BG).pack(side="left", padx=10)

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(pady=20)

        self.btn_prev = ctk.CTkButton(nav_frame, text="Back", command=lambda: self.app.load_screen("model"), fg_color=PANEL_BG, text_color=TEXT_COLOR)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(nav_frame, text="Next", command=lambda: self.handle_next(), fg_color=ACCENT_COLOR, text_color=BG_COLOR)
        self.btn_next.pack(side="left", padx=10)

    def handle_next(self):
        self.app.install_data["agents"] = list(self.selected_agents)
        self.app.load_screen("api_key")

    def populate_agents(self):
        for a in AGENTS:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR, border_width=1, border_color=MUTED_TEXT)
            card.pack(fill="x", pady=5, padx=5)
            var = ctk.BooleanVar(value=False)
            self.vars[a["name"]] = var
            def toggle(name=a["name"], v=var):
                if v.get(): self.selected_agents.add(name)
                else: self.selected_agents.discard(name)
            cb = ctk.CTkCheckBox(card, text=f"{a['icon']} {a['name']} - {a['desc']}", variable=var, command=toggle, font=FONT_MAIN, text_color=TEXT_COLOR, fg_color=ACCENT_COLOR)
            cb.pack(side="left", padx=10, pady=10)

    def select_all(self):
        for name, var in self.vars.items():
            var.set(True)
            self.selected_agents.add(name)

    def clear_all(self):
        for name, var in self.vars.items():
            var.set(False)
        self.selected_agents.clear()
