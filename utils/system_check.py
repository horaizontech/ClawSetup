import subprocess
import os
import shutil
import platform
import psutil
import socket
import re
from pathlib import Path

def get_os_info():
    """Returns dict with os name, version, architecture"""
    return {
        "os": platform.system(),
        "system": platform.system(), # Alias for compatibility
        "version": platform.version(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }

def check_ram():
    """Returns total RAM in GB"""
    return round(psutil.virtual_memory().total / (1024**3), 1)

def get_ram_info():
    """Alias for compatibility with existing code"""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 1),
        "available_gb": round(mem.available / (1024**3), 1)
    }

def check_disk_space(path=None):
    """Returns free disk space in GB for given path"""
    if path is None:
        path = Path.home()
    try:
        usage = psutil.disk_usage(str(path))
        return round(usage.free / (1024**3), 1)
    except Exception:
        return 0.0

def check_internet():
    """Returns True if internet is available"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except Exception:
        return False

def check_nodejs():
    """Returns Node.js version string or None"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def check_node_version():
    """Alias for compatibility, returns major version as int"""
    v = check_nodejs()
    if v:
        match = re.search(r'v(\d+)', v)
        if match:
            return int(match.group(1))
    return 0

def check_npm():
    """Returns npm version string or None"""
    try:
        # shell=True often needed for npm on Windows
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def check_git():
    """Returns git version string or None"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def check_python():
    """Returns True if Python 3.11+ is installed."""
    import sys
    return sys.version_info >= (3, 11)

def check_ollama():
    """Returns True if Ollama is running"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def check_openclaw():
    """Returns openclaw version string or None"""
    try:
        result = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_all_drives():
    """Returns list of dicts with drive info"""
    drives = []
    for partition in psutil.disk_partitions():
        try:
            # Skip CD-ROMs and other removable media that might throw errors if empty
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
            usage = psutil.disk_usage(partition.mountpoint)
            drives.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "total_gb": round(usage.total / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "used_percent": usage.percent
            })
        except Exception:
            pass
    return drives

def check_docker():
    """Legacy compatibility"""
    return shutil.which("docker") is not None
