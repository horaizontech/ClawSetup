import base64
import os
from pathlib import Path

# A tiny 1x1 transparent ICO base64 for fallback if no real icon exists
FALLBACK_ICON_B64 = "AAABAAEAAQEAAAEAIAAwAAAAFgAAACgAAAABAAAAAgAAAAEAIAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

def create_shortcuts(target_path: Path, log_callback) -> bool:
    log_callback("Creating Windows shortcuts...")
    try:
        import win32com.client
    except ImportError:
        log_callback("Error: pywin32 is not installed. Cannot create shortcuts via win32com.")
        return False

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Paths
        desktop = Path(shell.SpecialFolders("Desktop"))
        start_menu = Path(shell.SpecialFolders("Programs"))
        startup = Path(shell.SpecialFolders("Startup"))
        
        icon_path = target_path.parent / "assets" / "claw.ico"
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not icon_path.exists():
            log_callback("Writing embedded icon to assets...")
            with open(icon_path, "wb") as f:
                f.write(base64.b64decode(FALLBACK_ICON_B64))

        shortcuts_to_create = [
            (desktop / "OpenClaw.lnk", "OpenClaw Dashboard"),
            (start_menu / "OpenClaw.lnk", "OpenClaw Dashboard"),
            (startup / "OpenClawTray.lnk", "OpenClaw Tray Auto-Start")
        ]

        for lnk_path, desc in shortcuts_to_create:
            shortcut = shell.CreateShortCut(str(lnk_path))
            shortcut.Targetpath = str(target_path)
            shortcut.WorkingDirectory = str(target_path.parent)
            shortcut.IconLocation = str(icon_path)
            shortcut.Description = desc
            shortcut.save()
            log_callback(f"Created shortcut: {lnk_path}")

        return True
    except Exception as e:
        log_callback(f"Failed to create shortcuts: {e}")
        return False
