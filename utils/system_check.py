import platform
import subprocess
import psutil
import logging
from pathlib import Path

logger = logging.getLogger("ClawSetup.SystemCheck")

def get_os_info() -> dict:
    """Detects OS, release, and architecture."""
    logger.info("Detecting OS information.")
    return {
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine()
    }

def get_ram_info() -> dict:
    """Gets total and available RAM in GB."""
    logger.info("Checking RAM.")
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2)
    }

def check_command(cmd: list[str], timeout: int = 10) -> bool:
    """Helper to check if a CLI command runs successfully."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Command {' '.join(cmd)} failed or timed out: {e}")
        return False

def check_docker() -> bool:
    """Checks if Docker CLI is available."""
    logger.info("Checking for Docker.")
    return check_command(["docker", "--version"])

def check_python() -> bool:
    """Checks if Python is available."""
    logger.info("Checking for Python.")
    return check_command(["python", "--version"]) or check_command(["python3", "--version"])

def check_git() -> bool:
    """Checks if Git is available."""
    logger.info("Checking for Git.")
    return check_command(["git", "--version"])

def check_node() -> bool:
    """Checks if Node.js is available."""
    logger.info("Checking for Node.js.")
    return check_command(["node", "--version"])

def check_wsl2() -> bool:
    """Checks if WSL2 is installed (Windows only)."""
    if platform.system() != "Windows":
        return False
    logger.info("Checking for WSL2.")
    return check_command(["wsl", "--status"])
