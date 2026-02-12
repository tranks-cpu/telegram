import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Config:
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE: str = os.getenv("TELEGRAM_PHONE", "")
    SOURCE_CHANNELS: list[str] = [
        ch.strip()
        for ch in os.getenv("SOURCE_CHANNELS", "").split(",")
        if ch.strip()
    ]
    OUTPUT_CHANNEL: str = os.getenv("OUTPUT_CHANNEL", "")
    SESSION_FILE: str = str(DATA_DIR / "telegram_news")

    @classmethod
    def validate(cls) -> list[str]:
        errors = []
        if not cls.TELEGRAM_API_ID:
            errors.append("TELEGRAM_API_ID is required")
        if not cls.TELEGRAM_API_HASH:
            errors.append("TELEGRAM_API_HASH is required")
        if not cls.TELEGRAM_PHONE:
            errors.append("TELEGRAM_PHONE is required")
        if not cls.SOURCE_CHANNELS:
            errors.append("SOURCE_CHANNELS is required")
        if not cls.OUTPUT_CHANNEL:
            errors.append("OUTPUT_CHANNEL is required")
        return errors
