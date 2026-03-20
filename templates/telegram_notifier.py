import os
import requests
import logging
from pathlib import Path

logger = logging.getLogger("TelegramNotifier")
logging.basicConfig(level=logging.INFO)

class TelegramNotifier:
    def __init__(self, env_path: str = ".env"):
        self.token = None
        self.chat_id = None
        self.prefs = {}
        self._load_config(env_path)

    def _load_config(self, env_path: str):
        path = Path(env_path)
        if path.exists():
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        if key == "TELEGRAM_BOT_TOKEN":
                            self.token = val
                        elif key == "TELEGRAM_CHAT_ID":
                            self.chat_id = val
                        elif key.startswith("TELEGRAM_NOTIFY_"):
                            self.prefs[key] = (val.lower() == "true")
        else:
            logger.warning(f"Config file {env_path} not found. Falling back to environment variables.")
            
        # Fallback to environment variables if not set in file
        if not self.token:
            self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.chat_id:
            self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        for key in ["TELEGRAM_NOTIFY_START", "TELEGRAM_NOTIFY_COMPLETE", "TELEGRAM_NOTIFY_FAIL", "TELEGRAM_NOTIFY_SWITCH", "TELEGRAM_NOTIFY_FILE"]:
            if key not in self.prefs and key in os.environ:
                self.prefs[key] = (os.environ.get(key, "").lower() == "true")

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured():
            logger.warning("Telegram not configured. Skipping message.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def notify_task_started(self, task_desc: str):
        if self.prefs.get("TELEGRAM_NOTIFY_START", True):
            self.send_message(f"🚀 *Task Started*\n\n{task_desc}")

    def notify_task_completed(self, task_desc: str, result: str):
        if self.prefs.get("TELEGRAM_NOTIFY_COMPLETE", True):
            self.send_message(f"✅ *Task Completed*\n\n*Task:* {task_desc}\n*Result:* {result}")

    def notify_task_failed(self, task_desc: str, error: str):
        if self.prefs.get("TELEGRAM_NOTIFY_FAIL", True):
            self.send_message(f"❌ *Task Failed*\n\n*Task:* {task_desc}\n*Error:* {error}")

    def notify_agent_switched(self, old_agent: str, new_agent: str, reason: str):
        if self.prefs.get("TELEGRAM_NOTIFY_SWITCH", True):
            self.send_message(f"🔄 *Agent Switched*\n\n*From:* {old_agent}\n*To:* {new_agent}\n*Reason:* {reason}")

    def notify_file_created(self, filepath: str):
        if self.prefs.get("TELEGRAM_NOTIFY_FILE", True):
            self.send_message(f"📄 *New File Created*\n\n`{filepath}`")

if __name__ == "__main__":
    # Simple test execution if run directly
    notifier = TelegramNotifier()
    if notifier.is_configured():
        notifier.send_message("🤖 *OpenClaw Telegram Notifier* is online and configured correctly.")
    else:
        print("Telegram is not configured in .env")
