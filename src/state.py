import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

STATE_FILE = DATA_DIR / "state.json"


def load_last_run() -> datetime:
    """Load last_run timestamp from state file. Returns 24h ago if not found."""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            return datetime.fromisoformat(data["last_run"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load state: {e}")

    # Default: 24 hours ago
    return datetime.now(timezone.utc) - timedelta(hours=24)


def save_last_run(dt: datetime | None = None) -> None:
    """Save current timestamp to state file."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    STATE_FILE.write_text(json.dumps({"last_run": dt.isoformat()}, indent=2))
    logger.info(f"Saved last_run: {dt.isoformat()}")
