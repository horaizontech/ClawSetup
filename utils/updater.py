import requests
import threading
import customtkinter as ctk

GITHUB_REPO = "OpenClaw/ClawSetup" # Updated from placeholder
CURRENT_VERSION = "v1.0.0"

def check_for_updates(callback):
    """
    Checks the GitHub releases API for a newer version.
    Runs asynchronously and calls `callback(new_version_str, release_url)` if found.
    """
    def _check():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "")
                release_url = data.get("html_url", "")
                
                if latest_version and latest_version != CURRENT_VERSION:
                    # Very simple version comparison (assumes vX.Y.Z format)
                    callback(latest_version, release_url)
        except Exception as e:
            print(f"Update check failed: {e}")

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()

def show_update_banner(parent, new_version, release_url):
    """
    Displays a banner at the top of the given parent window.
    """
    banner = ctk.CTkFrame(parent, fg_color="#FFD700", corner_radius=0, height=40)
    banner.pack(fill="x", side="top")
    
    lbl = ctk.CTkLabel(banner, text=f"A new version of ClawSetup ({new_version}) is available!", text_color="#000000", font=("Roboto", 12, "bold"))
    lbl.pack(side="left", padx=20, pady=10)
    
    def open_release():
        import webbrowser
        webbrowser.open(release_url)
        
    btn = ctk.CTkButton(banner, text="Download Update", command=open_release, fg_color="#000000", hover_color="#333333", text_color="#FFFFFF", width=120, height=28)
    btn.pack(side="right", padx=20, pady=6)
    
    def close_banner():
        banner.destroy()
        
    close_btn = ctk.CTkButton(banner, text="X", command=close_banner, fg_color="transparent", hover_color="#E6C200", text_color="#000000", width=28, height=28)
    close_btn.pack(side="right", padx=(0, 10), pady=6)
