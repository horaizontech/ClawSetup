import subprocess
import time
import platform
import urllib.request
import zipfile
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

def install_ollama_windows(install_dir: Path, log_callback) -> bool:
    url = "https://ollama.com/download/ollama-windows-amd64.zip"
    zip_path = install_dir / "ollama.zip"
    
    log_callback(f"Downloading Ollama for Windows from {url}...")
    try:
        urllib.request.urlretrieve(url, str(zip_path))
        log_callback("Download complete. Extracting...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(str(install_dir))
        
        zip_path.unlink()
        log_callback(f"Extracted to {install_dir}")
        
        # Add to PATH via Registry
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            current_path = ""
            
        if str(install_dir) not in current_path:
            new_path = f"{current_path};{install_dir}" if current_path else str(install_dir)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            log_callback("Added Ollama to user PATH.")
        winreg.CloseKey(key)
        
        # Start serve
        subprocess.Popen([str(install_dir / "ollama.exe"), "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        return True
    except Exception as e:
        log_callback(f"Failed to install Ollama on Windows: {e}")
        return False

def setup_ollama(install_dir: Path, log_callback) -> bool:
    sys_name = platform.system()
    if sys_name == "Windows":
        return install_ollama_windows(install_dir, log_callback)
    elif sys_name == "Darwin":
        try:
            from platforms.macos.ollama_mac import install_ollama_mac
            return install_ollama_mac(log_callback)
        except ImportError:
            log_callback("Error: macOS ollama module not found.")
            return False
    else:
        log_callback(f"Ollama auto-install not supported on {sys_name}.")
        return False

def pull_models(models: list[str], log_callback) -> bool:
    log_callback(f"Starting pull for {len(models)} models...")
    all_success = True
    for model in models:
        log_callback(f"--- Pulling model: {model} ---")
        # 1800 seconds = 30 mins timeout for large models
        success = run_with_stream(["ollama", "pull", model], log_callback, timeout=1800)
        if not success:
            log_callback(f"Failed to pull {model}.")
            all_success = False
        else:
            log_callback(f"Successfully pulled {model}.")
    return all_success
