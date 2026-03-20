import subprocess
import time
from pathlib import Path

def run_with_stream(cmd: list[str], log_callback, timeout: int = 300) -> bool:
    """Runs a command, streams stdout to callback, enforces timeout."""
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        start_time = time.time()
        for line in iter(process.stdout.readline, ''):
            if line:
                log_callback(line.strip())
            if time.time() - start_time > timeout:
                process.kill()
                log_callback(f"Error: Command timed out after {timeout} seconds.")
                return False
        process.wait()
        return process.returncode == 0
    except Exception as e:
        log_callback(f"Exception running command: {e}")
        return False

def is_wsl_enabled(log_callback) -> bool:
    log_callback("Checking if WSL2 is enabled...")
    try:
        result = subprocess.run(["wsl", "--status"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log_callback("WSL2 is already enabled and functional.")
            return True
        return False
    except FileNotFoundError:
        return False
    except Exception as e:
        log_callback(f"Error checking WSL status: {e}")
        return False

def install_wsl(log_callback) -> bool:
    if is_wsl_enabled(log_callback):
        return True
        
    log_callback("WSL2 not found. Initiating installation (may prompt for UAC elevation)...")
    # Use PowerShell to trigger UAC
    cmd = [
        "powershell", "-NoProfile", "-Command",
        "Start-Process wsl -ArgumentList '--install' -Verb RunAs -Wait"
    ]
    success = run_with_stream(cmd, log_callback, timeout=600)
    
    if success:
        log_callback("WSL installation command completed. Verifying...")
        time.sleep(5)
        if is_wsl_enabled(log_callback):
            log_callback("WSL2 successfully installed and verified.")
            return True
        else:
            log_callback("WSL2 installation finished but verification failed. A system reboot might be required.")
            return False
    else:
        log_callback("Failed to install WSL2.")
        return False
