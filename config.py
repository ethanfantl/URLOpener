import logging
import customtkinter as ctk

# Database Config
DB_NAME = "url_manager.db"

# UI Config
THEME_MODE = "System"
THEME_COLOR = "blue"

# Logging Config
LOG_FILE = "app_debug.log"
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )

def setup_theme():
    ctk.set_appearance_mode(THEME_MODE)
    ctk.set_default_color_theme(THEME_COLOR)