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

def install_ollama_mac(log_callback) -> bool:
    # Check if installed
    try:
        res = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            log_callback("Ollama is already installed.")
            return start_ollama_serve(log_callback)
    except FileNotFoundError:
        pass

    url = "https://ollama.com/download/Ollama-darwin.pkg"
    pkg_path = Path.home() / "Downloads" / "Ollama.pkg"
    
    log_callback(f"Downloading Ollama macOS installer from {url}...")
    try:
        urllib.request.urlretrieve(url, str(pkg_path))
        log_callback("Download complete.")
    except Exception as e:
        log_callback(f"Failed to download Ollama: {e}")
        return False

    log_callback("Installing Ollama (requires privileges, may prompt via terminal)...")
    log_callback("NOTE: If this hangs, please install Ollama manually from ollama.com")
    cmd = ["sudo", "-n", "installer", "-pkg", str(pkg_path), "-target", "/"]
    if not run_with_stream(cmd, log_callback, timeout=300):
        log_callback("Failed to install Ollama.")
        return False

    return start_ollama_serve(log_callback)

def start_ollama_serve(log_callback) -> bool:
    log_callback("Starting Ollama service in background...")
    try:
        # Start as daemon
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # Verify
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            log_callback("Ollama service is running.")
            return True
        else:
            log_callback("Ollama service failed to respond to 'list' command.")
            return False
    except Exception as e:
        log_callback(f"Failed to start Ollama: {e}")
        return False
