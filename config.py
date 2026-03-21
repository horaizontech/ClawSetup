import logging
from pathlib import Path

APP_NAME = "ClawSetup"
VERSION = "v1.0.0"

# OpenClaw Configuration
OPENCLAW_IMAGE = "alpine/openclaw:latest"
OPENCLAW_DEFAULT_PORT = 18789
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
logger.info(f"Initialized {APP_NAME} v{VERSION} configuration.")
