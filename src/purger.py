import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

HISTORY_DIR = Path("data/history")
RETENTION_DAYS = 7


def purge():
    if not HISTORY_DIR.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    for f in HISTORY_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff:
                f.unlink()
                print(f"Purged: {f.name}")
        except ValueError:
            f.unlink()
