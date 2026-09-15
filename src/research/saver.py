"""
Save papers to JSON file.
"""
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def save_papers(papers, path=None):
    if path is None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        path = os.path.join(DATA_DIR, f"papers-{today}.json")

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    latest_path = os.path.join(DATA_DIR, "papers-latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"[saver] Saved {len(papers)} papers to {path}")
    return path