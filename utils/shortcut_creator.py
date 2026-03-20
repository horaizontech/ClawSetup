import platform
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("ClawSetup.ShortcutCreator")

def create_windows_shortcut(target_path: str, shortcut_name: str) -> bool:
    """Creates a Windows desktop shortcut (.lnk)."""
    logger.info(f"Creating Windows shortcuts for {target_path}")
    try:
        from platforms.windows.shortcut_windows import create_shortcuts
        def log_cb(msg):
            logger.info(msg)
        return create_shortcuts(Path(target_path), log_cb)
    except Exception as e:
        logger.error(f"Failed to create Windows shortcut: {e}")
        return False

def create_mac_shortcut(target_path: str, shortcut_name: str) -> bool:
    """Creates a macOS desktop alias."""
    logger.info(f"Creating macOS shortcut for {target_path}")
    target = Path(target_path)
    desktop = Path.home() / "Desktop"
    alias_path = desktop / f"{shortcut_name}"
    
    applescript = f'''
    tell application "Finder"
        make alias file to POSIX file "{target}" at POSIX file "{desktop}"
        set name of result to "{shortcut_name}"
    end tell
    '''
    try:
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            logger.info(f"Shortcut created at {alias_path}")
            return True
        else:
            logger.error(f"Failed to create Mac shortcut: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout creating Mac shortcut.")
        return False

def create_desktop_shortcut(target_path: str, shortcut_name: str = "OpenClaw") -> bool:
    """Creates a desktop shortcut based on the OS."""
    sys_name = platform.system()
    if sys_name == "Windows":
        return create_windows_shortcut(target_path, shortcut_name)
    elif sys_name == "Darwin":
        return create_mac_shortcut(target_path, shortcut_name)
    else:
        logger.warning(f"Shortcut creation not supported on {sys_name}")
        return False
