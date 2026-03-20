@echo off
echo Building ClawSetup for Windows...
pyinstaller --onefile --windowed --name ClawSetup --icon=assets/claw.ico --add-data "templates;templates" --add-data "assets;assets" --hidden-import customtkinter --hidden-import PIL --hidden-import psutil --hidden-import requests --hidden-import pystray --hidden-import win32com --hidden-import win32com.client main.py
echo Build complete. Check the dist/ folder.
pause
