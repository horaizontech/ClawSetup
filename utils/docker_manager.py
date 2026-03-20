import subprocess
import logging
import platform
import time
from pathlib import Path

logger = logging.getLogger("ClawSetup.DockerManager")

def ensure_docker_running(log_callback=None):
    """Start Docker Desktop if not running and wait until it is ready."""
    def log(msg):
        if log_callback:
            log_callback(msg)
        logger.info(msg)
    
    # Step 1: Check if Docker is already running
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            log("Docker is already running.")
            return True
    except Exception:
        pass
    
    # Step 2: Try to start Docker Desktop
    log("Docker not running. Attempting to start Docker Desktop...")
    
    if platform.system() == "Windows":
        docker_paths = [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
        ]
        started = False
        for path in docker_paths:
            if Path(path).exists():
                subprocess.Popen([path])
                started = True
                log(f"Started Docker Desktop from {path}")
                break
        if not started:
            log("ERROR: Docker Desktop not found. Please install Docker Desktop first.")
            return False
    
    elif platform.system() == "Darwin":
        try:
            subprocess.Popen(["open", "-a", "Docker"])
            log("Started Docker Desktop on macOS")
        except Exception as e:
            log(f"ERROR: Failed to start Docker on macOS: {e}")
            return False
    
    # Step 3: Wait for Docker to be ready — poll every 5 seconds for up to 3 minutes
    log("Waiting for Docker to be ready (this may take up to 3 minutes)...")
    for attempt in range(36):  # 36 x 5 seconds = 3 minutes
        time.sleep(5)
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log(f"Docker is ready after {(attempt+1)*5} seconds.")
                return True
            else:
                log(f"Still waiting for Docker... ({(attempt+1)*5}s)")
        except Exception:
            log(f"Still waiting for Docker... ({(attempt+1)*5}s)")
    
    log("ERROR: Docker did not start within 3 minutes. Please start Docker Desktop manually and retry.")
    return False

def pull_image(image_name: str, log_callback=None) -> bool:
    """Pulls a Docker image."""
    logger.info(f"Pulling Docker image: {image_name}")
    try:
        process = subprocess.Popen(["docker", "pull", image_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        start_time = time.time()
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.strip()
                logger.info(line)
                if log_callback:
                    log_callback(line)
            if time.time() - start_time > 1800: # 30 mins
                process.kill()
                logger.error("Timeout pulling image.")
                if log_callback:
                    log_callback("Error: Timeout pulling image.")
                return False
        process.wait()
        return process.returncode == 0
    except Exception as e:
        logger.error(f"Exception pulling {image_name}: {e}")
        return False
