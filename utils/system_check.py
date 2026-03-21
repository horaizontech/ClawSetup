import subprocess
import os
import shutil
import platform
import psutil
import re

def check_python():
    """Check if Python 3.11+ is installed."""
    try:
        import sys
        return sys.version_info >= (3, 11)
    except:
        return False

def check_git():
    """Check if Git is installed."""
    return shutil.which("git") is not None

def check_node_version():
    """Check Node.js version. Returns major version as int or 0."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip()
        # Matches v22.14.0 -> 22
        match = re.search(r'v(\d+)', version)
        if match:
            return int(match.group(1))
    except:
        pass
    return 0

def get_ram_info():
    """Get system RAM info."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 1),
        "available_gb": round(mem.available / (1024**3), 1)
    }

def check_docker():
    """Legacy: check if Docker is installed."""
    return shutil.which("docker") is not None
