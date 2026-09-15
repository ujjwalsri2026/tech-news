import os
import glob
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path("data")
NEWS_RETENTION_DAYS = 7
RESEARCH_RETENTION_DAYS = 30


def purge():
    if not DATA_DIR.exists():
        return

    # ─── Purge old news files (data/digest-*.json) ───
    cutoff_news = datetime.now(timezone.utc) - timedelta(days=NEWS_RETENTION_DAYS)
    for f in DATA_DIR.glob("digest-*.json"):
        try:
            file_date = datetime.strptime(f.stem, "digest-%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff_news:
                f.unlink()
                print(f"[purger] Removed news: {f.name}")
        except ValueError:
            pass

    # ─── Purge old research files (data/papers-*.json) ───
    cutoff_research = datetime.now(timezone.utc) - timedelta(days=RESEARCH_RETENTION_DAYS)
    for f in DATA_DIR.glob("papers-????-??-??.json"):
        try:
            file_date = datetime.strptime(f.stem, "papers-%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff_research:
                f.unlink()
                print(f"[purger] Removed research: {f.name}")
        except ValueError:
            pass

    # ─── Legacy: purge data/history/ if exists ───
    history_dir = DATA_DIR / "history"
    if history_dir.exists():
        cutoff_legacy = datetime.now(timezone.utc) - timedelta(days=NEWS_RETENTION_DAYS)
        for f in history_dir.glob("*.json"):
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if file_date < cutoff_legacy:
                    f.unlink()
                    print(f"[purger] Removed legacy: {f.name}")
            except ValueError:
                f.unlink()
