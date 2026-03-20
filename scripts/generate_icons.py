import os
import requests
from PIL import Image, ImageDraw

def generate_icon_pillow():
    print("Generating simple programmatic icon using Pillow...")
    os.makedirs("assets", exist_ok=True)
    img = Image.new("RGBA", (256, 256), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)
    # Draw simple claw-like shapes
    draw.ellipse([60, 60, 196, 196], fill=(0, 245, 255, 255))
    draw.ellipse([90, 90, 166, 166], fill=(13, 17, 23, 255))
    
    img.save("assets/claw.png")
    img.save("assets/claw.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
    print("Icons generated successfully via Pillow fallback.")

def download_icon():
    url = "https://www.iconsdb.com/icons/download/black/claw-marks-ico.ico"
    print(f"Attempting to download icon from {url}...")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs("assets", exist_ok=True)
            with open("assets/claw.ico", "wb") as f:
                f.write(response.content)
            # Also create a PNG version
            img = Image.open("assets/claw.ico")
            img.save("assets/claw.png")
            print("Icon downloaded and converted successfully.")
            return True
    except Exception as e:
        print(f"Download failed: {e}")
    return False

if __name__ == "__main__":
    if not download_icon():
        generate_icon_pillow()
        
    if os.path.exists("assets/claw.ico"):
        size = os.path.getsize("assets/claw.ico")
        print(f"Final assets/claw.ico size: {size} bytes")
