#!/bin/bash
echo "Building ClawSetup for macOS..."
pyinstaller --onefile --windowed --name ClawSetup --icon=assets/claw.icns --add-data "templates:templates" --add-data "assets:assets" --hidden-import customtkinter --hidden-import PIL --hidden-import psutil --hidden-import requests --hidden-import pystray main.py
echo "Build complete. Check the dist/ folder."
