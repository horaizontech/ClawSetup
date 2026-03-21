import os
import logging
from pathlib import Path

# App Info
APP_NAME = "ClawSetup"
APP_VERSION = "1.0.0"

# OpenClaw Configuration (Primary)
OPENCLAW_IMAGE = "alpine/openclaw:latest"
OPENCLAW_DEFAULT_PORT = 18789

# OpenHands Compatibility Aliases (to prevent ImportErrors)
OPENHANDS_IMAGE = "alpine/openclaw:latest"
OPENHANDS_RUNTIME_IMAGE = "alpine/openclaw:latest"
OPENHANDS_DASHBOARD_PORT = 18789

# Paths
BASE_DIR = Path(__file__).parent.resolve()

# Centralized config in user home
CONFIG_ROOT = Path.home() / ".clawsetup"
CONFIG_ROOT.mkdir(exist_ok=True)

INSTALL_STATE_FILE = CONFIG_ROOT / "install_state.json"
TEMPLATES_DIR = BASE_DIR / "templates"
AGENTS_DIR = TEMPLATES_DIR / "agents"
ASSETS_DIR = BASE_DIR / "assets"

# Logging setup
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "setup.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(APP_NAME)
logger.info(f"Initialized {APP_NAME} v{APP_VERSION} configuration.")
