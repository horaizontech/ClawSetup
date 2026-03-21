import logging
from pathlib import Path

APP_NAME = "ClawSetup"
VERSION = "v1.0.0"

# OpenHands Configuration
OPENHANDS_IMAGE = "docker.all-hands.dev/all-hands-ai/openhands:0.62"
OPENHANDS_RUNTIME_IMAGE = "docker.all-hands.dev/all-hands-ai/runtime:0.62-nikolaik"
OPENHANDS_DASHBOARD_PORT = 3000

# Legacy compatibility (to be removed once fully pivoted)
OPENCLAW_IMAGE = OPENHANDS_IMAGE
OPENCLAW_DEFAULT_PORT = 3000
OPENCLAW_DASHBOARD_PATH = "/"

# Paths
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "setup.log"
INSTALL_STATE_FILE = BASE_DIR / "install_state.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(APP_NAME)
logger.info(f"Initialized {APP_NAME} v{VERSION} configuration for OpenHands.")
