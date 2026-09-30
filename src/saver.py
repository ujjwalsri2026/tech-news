import json
from datetime import datetime, timezone
from pathlib import Path

from src.purger import purge

SUMMARIES_PATH = Path("data/summaries.json")


def save(results: list[dict]):
    now = datetime.now(timezone.utc).isoformat()
    sources = len({r["source"] for r in results})
    payload = {
        "generated_at": now,
        "source_count": sources,
        "article_count": len(results),
        "items": results,
    }
    SUMMARIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARIES_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    purge()
