import json
from pathlib import Path


def load_urls(path: str = "data/urls.json") -> list[dict]:
    return json.loads(Path(path).read_text())


def load_summaries(path: str = "data/summaries.json") -> dict:
    p = Path(path)
    if not p.exists():
        return {"generated_at": None, "count": 0, "items": []}
    return json.loads(p.read_text())
