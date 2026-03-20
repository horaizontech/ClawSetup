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

def create_mac_shortcuts(target_script: Path, log_callback) -> bool:
    log_callback("Creating macOS shortcuts and launchers...")
    
    app_dir = Path.home() / "Applications" / "ClawSetup"
    app_dir.mkdir(parents=True, exist_ok=True)
    
    command_script = app_dir / "OpenClaw.command"
    
    script_content = f"""#!/bin/bash
echo "Starting OpenClaw..."
python3 "{target_script}"
"""
    try:
        with open(command_script, "w") as f:
            f.write(script_content)
        command_script.chmod(0o755)
        log_callback(f"Created launcher script at {command_script}")
    except Exception as e:
        log_callback(f"Failed to create launcher script: {e}")
        return False

    # Create Dock alias via AppleScript
    applescript = f'''
    tell application "System Events"
        if not (exists login item "OpenClaw") then
            make login item at end with properties {{path:"{command_script}", hidden:false, name:"OpenClaw"}}
        end if
    end tell
    '''
    log_callback("Adding to Login Items (Startup)...")
    run_with_stream(["osascript", "-e", applescript], log_callback, 30)

    # Create LaunchAgent plist
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{command_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.openclaw.launcher.plist"
    try:
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plist_path, "w") as f:
            f.write(plist_content)
        log_callback(f"Created LaunchAgent at {plist_path}")
    except Exception as e:
        log_callback(f"Failed to create LaunchAgent: {e}")

    return True
