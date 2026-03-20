# ClawSetup Fixes Log

This file tracks every change made to the ClawSetup codebase to address the issues identified in the audit.

| File | Change Description | Type | Rationale |
| :--- | :--- | :--- | :--- |
| `FIXES_LOG.md` | Initialized fix tracking. | New | Compliance with user request. |
| `gui/theme.py` | Implemented `set_theme()` function. | Surgical | Fixed broken import and call in `main.py`. |
| `main.py` | Rewrote entire file to fix imports, paths, and implement basic uninstall logic. | Rewrite | Resolved >3 architectural issues identified in audit. |
| `config.py` | Synchronized `VERSION` with `updater.py` format ("v1.0.0"). | Surgical | Resolved versioning inconsistency. |
| `gui/screen_requirements.py` | Rewrote file to implement actual system checks (disk, internet, WSL2) and auto-installers. | Rewrite | Removed placeholders and implemented functional requirements logic. |
| `gui/screen_model_selector.py` | Used `LOCALAPPDATA` for Ollama path on Windows; added missing `os` import. | Surgical | Improved path robustness and fixed a potential runtime error. |
| `gui/screen_install.py` | Rewrote file to use absolute paths for templates, added guards for empty selection lists, and improved Docker subprocess calls. | Rewrite | Fixed path sensitivity and improved stability during installation. |
| `utils/error_handler.py` | Cleaned up brittle `sys.path` injections and parameterized log directory using `config.BASE_DIR`. | Surgical | Improved modularity and alignment with project structure. |
| `utils/updater.py` | Updated `GITHUB_REPO` and synchronized `CURRENT_VERSION` format. | Surgical | Fixed placeholders and versioning. |
| `utils/docker_manager.py` | Parameterized Docker Desktop path using `ProgramFiles` environment variable on Windows. | Surgical | Removed hardcoded absolute paths. |
| `utils/health_check.py` | Fixed mismatched key check (added support for `"name"` in addition to `"agent_name"`) and improved API error handling. | Surgical | Resolved critical bug where health checks always failed for agents. |
| `platforms/windows/docker_windows.py` | Parameterized installer download paths using `TEMP` directory. | Surgical | Removed hardcoded 'Downloads' path. |
| `platforms/windows/firewall_windows.py` | Parameterized Docker path using `ProgramFiles` environment variable. | Surgical | Removed hardcoded absolute paths. |
| `platforms/macos/ollama_mac.py` | Added safety warnings and non-interactive flag for `sudo` installation commands. | Surgical | Prevented GUI hangs during installation. |
| `assets/icons.py` | Updated icon base64 placeholders to functional stubs. | Surgical | Cleaned up placeholder comments. |
| `templates/agents/*.json` | Updated all 10 agent templates to use `"agent_name"` key for compatibility with health check system. | Surgical | Resolved key name mismatch across the template library. |
| `requirements.txt` | Removed unused `docker` Python package; synchronized with actual imports. | Cleanup | Reduced dependency bloat and matched code usage. |
