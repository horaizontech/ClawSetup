BG_COLOR = "#0D1117"
ACCENT_COLOR = "#00F5FF"
SUCCESS_COLOR = "#39FF14"
ERROR_COLOR = "#FF4444"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#8B949E"
PANEL_BG = "#161B22"

FONT_MAIN = ("Roboto", 14)
FONT_HEADING = ("Roboto", 24, "bold")
FONT_MONO = ("JetBrains Mono", 12)

def set_theme():
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue") # Or a custom json if available
