import subprocess
import logging
import requests
import platform
from pathlib import Path

logger = logging.getLogger("ClawSetup.OllamaManager")

OLLAMA_API_URL = "http://127.0.0.1:11434/api"

def is_ollama_installed() -> bool:
    """Checks if Ollama CLI is available."""
    logger.info("Checking if Ollama is installed.")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def is_ollama_running() -> bool:
    """Checks if Ollama API is responding."""
    logger.info("Checking if Ollama service is running.")
    try:
        response = requests.get("http://127.0.0.1:11434/", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_available_models() -> list[str]:
    """Lists locally available Ollama models."""
    logger.info("Fetching available Ollama models.")
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
    except requests.RequestException as e:
        logger.error(f"Failed to fetch models: {e}")
    return []

def pull_model(model_name: str, log_callback=None) -> bool:
    """Pulls an Ollama model."""
    logger.info(f"Pulling Ollama model: {model_name}")
    try:
        process = subprocess.Popen(["ollama", "pull", model_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        import time
        start_time = time.time()
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.strip()
                logger.info(line)
                if log_callback:
                    log_callback(line)
            if time.time() - start_time > 1800:
                process.kill()
                logger.error(f"Timeout pulling model {model_name}")
                if log_callback:
                    log_callback(f"Error: Timeout pulling model {model_name}")
                return False
        process.wait()
        if process.returncode == 0:
            logger.info(f"Successfully pulled model {model_name}")
            return True
        else:
            logger.error(f"Failed to pull model {model_name}")
            return False
    except Exception as e:
        logger.error(f"Exception pulling model {model_name}: {e}")
        return False
