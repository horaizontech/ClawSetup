import subprocess
import time
import urllib.request
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

def download_docker(dest_path: Path, log_callback) -> bool:
    url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    log_callback(f"Downloading Docker Desktop from {url}...")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
        log_callback("Download complete.")
        return True
    except Exception as e:
        log_callback(f"Failed to download Docker Desktop: {e}")
        return False

def install_docker(log_callback) -> bool:
    temp_dir = Path(os.environ.get("TEMP", "."))
    installer_path = temp_dir / "DockerDesktopInstaller.exe"
    
    # Check if already installed
    try:
        res = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            log_callback("Docker is already installed.")
            return wait_for_docker(log_callback)
    except FileNotFoundError:
        pass

    if not installer_path.exists():
        if not download_docker(installer_path, log_callback):
            return False

    log_callback("Installing Docker Desktop silently (requires UAC elevation)...")
    cmd = [
        "powershell", "-NoProfile", "-Command",
        f"Start-Process '{installer_path}' -ArgumentList 'install --quiet --accept-license' -Verb RunAs -Wait"
    ]
    
    if not run_with_stream(cmd, log_callback, timeout=900):
        log_callback("Docker installation failed.")
        return False
        
    log_callback("Docker installed. Waiting for service to start...")
    return wait_for_docker(log_callback)

def wait_for_docker(log_callback, max_retries=30) -> bool:
    for i in range(max_retries):
        try:
            res = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                log_callback("Docker service is running and ready.")
                return True
        except Exception:
            pass
        log_callback(f"Waiting for Docker to start... (Attempt {i+1}/{max_retries})")
        time.sleep(5)
        
    log_callback("Error: Docker service did not start in time. Please start it manually.")
    return False
