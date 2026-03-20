# ClawSetup

**ClawSetup** is a custom PyQt/CustomTkinter based GUI installer for **OpenClaw** (the OpenHands AI agent platform). It simplifies the setup process by automating the installation of Docker, WSL2, and LLM models via Ollama.

## Features
- Multi-step installation wizard.
- Automated system requirements check (Docker, Git, RAM, Disk).
- Platform-specific installers for Windows and macOS.
- Local LLM model selection and setup.
- Desktop shortcut and system tray launcher.
- Telegram notification integration for installation events.

## Prerequisites
- Windows 10/11 or macOS.
- Python 3.11+ (recommended).

## How to Run from Source
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## How to Build Executable
### Windows
Run the provided batch file:
```bash
build_windows.bat
```

### macOS
Run the provided shell script:
```bash
./build_mac.sh
```

## Project Structure
- `gui/`: Screen implementations and theme definitions.
- `platforms/`: OS-specific installation logic.
- `utils/`: Core utilities (Docker manager, updater, etc.).
- `templates/`: Configuration and agent profile templates.
- `assets/`: Embedded icons and graphics.

## License
MIT
