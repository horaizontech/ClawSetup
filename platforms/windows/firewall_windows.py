import subprocess
import time
from pathlib import Path

def run_with_stream(cmd: list[str], log_callback, timeout: int = 300) -> bool:
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

def configure_firewall(port: int, log_callback) -> bool:
    log_callback(f"Configuring Windows Firewall for port {port} (requires UAC)...")
    
    # Rule for the specific port
    port_cmd = f"netsh advfirewall firewall add rule name='OpenClaw Dashboard' dir=in action=allow protocol=TCP localport={port}"
    
    # Rule for Docker (searching common paths)
    prog_files = os.environ.get("ProgramFiles", "C:/Program Files")
    docker_path = Path(prog_files) / "Docker" / "Docker" / "Docker Desktop.exe"
    docker_cmd = f"netsh advfirewall firewall add rule name='Docker Desktop' dir=in action=allow program='{docker_path}' enable=yes"

    full_cmd = f"{port_cmd} ; {docker_cmd}"
    
    cmd = [
        "powershell", "-NoProfile", "-Command",
        f"Start-Process powershell -ArgumentList '-NoProfile -Command \"{full_cmd}\"' -Verb RunAs -Wait"
    ]
    
    success = run_with_stream(cmd, log_callback, timeout=120)
    if success:
        log_callback("Firewall rules added successfully.")
    else:
        log_callback("Failed to add firewall rules. You may need to allow access manually.")
    
    return success
