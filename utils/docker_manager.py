import subprocess
import logging
import platform
from pathlib import Path

logger = logging.getLogger("ClawSetup.DockerManager")

def is_docker_running() -> bool:
    """Checks if the Docker daemon is responding."""
    logger.info("Checking if Docker is running.")
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=15)
        is_running = result.returncode == 0
        logger.info(f"Docker running status: {is_running}")
        return is_running
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Failed to check Docker status: {e}")
        return False

def start_docker_desktop() -> bool:
    """Attempts to start Docker Desktop based on the OS."""
    logger.info("Attempting to start Docker Desktop.")
    sys_name = platform.system()
    try:
        if sys_name == "Windows":
            program_files = os.environ.get("ProgramFiles", "C:/Program Files")
            docker_path = Path(program_files) / "Docker" / "Docker" / "Docker Desktop.exe"
            if docker_path.exists():
                subprocess.Popen([str(docker_path)])
                return True
        elif sys_name == "Darwin":
            subprocess.run(["open", "-a", "Docker"], capture_output=True, timeout=15)
            return True
        else:
            logger.warning("Auto-start not supported on this OS.")
            return False
    except Exception as e:
        logger.error(f"Error starting Docker: {e}")
    return False

def pull_image(image_name: str, log_callback=None) -> bool:
    """Pulls a Docker image."""
    logger.info(f"Pulling Docker image: {image_name}")
    try:
        # Timeout set high for large image downloads
        process = subprocess.Popen(["docker", "pull", image_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        import time
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
        if process.returncode == 0:
            logger.info(f"Successfully pulled {image_name}")
            return True
        else:
            logger.error(f"Failed to pull {image_name}")
            return False
    except Exception as e:
        logger.error(f"Exception pulling {image_name}: {e}")
        return False
