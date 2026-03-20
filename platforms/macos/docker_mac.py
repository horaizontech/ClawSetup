import subprocess
import time
import platform
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

def install_docker_mac(log_callback) -> bool:
    # Check if installed
    app_path = Path("/Applications/Docker.app")
    if app_path.exists():
        log_callback("Docker Desktop is already installed in /Applications.")
        return start_and_wait_docker(log_callback)

    arch = platform.machine()
    if arch == "arm64":
        url = "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
    else:
        url = "https://desktop.docker.com/mac/main/amd64/Docker.dmg"

    dmg_path = Path.home() / "Downloads" / "Docker.dmg"
    log_callback(f"Downloading Docker Desktop for {arch} from {url}...")
    
    try:
        urllib.request.urlretrieve(url, str(dmg_path))
        log_callback("Download complete.")
    except Exception as e:
        log_callback(f"Failed to download Docker: {e}")
        return False

    log_callback("Mounting Docker.dmg...")
    if not run_with_stream(["hdiutil", "attach", str(dmg_path), "-nobrowse"], log_callback, 120):
        return False

    log_callback("Copying Docker.app to /Applications (this may take a moment)...")
    # The volume name is usually "Docker"
    vol_path = Path("/Volumes/Docker/Docker.app")
    if not run_with_stream(["cp", "-R", str(vol_path), "/Applications/"], log_callback, 300):
        log_callback("Failed to copy Docker.app")
        return False

    log_callback("Unmounting Docker.dmg...")
    run_with_stream(["hdiutil", "detach", "/Volumes/Docker"], log_callback, 60)

    return start_and_wait_docker(log_callback)

def start_and_wait_docker(log_callback, max_retries=30) -> bool:
    log_callback("Launching Docker Desktop...")
    run_with_stream(["open", "-a", "Docker"], log_callback, 30)
    
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
        
    log_callback("Error: Docker service did not start in time.")
    return False
