"""
Load papers from JSON file.
"""
import json
import os
import glob

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load_latest():
    path = os.path.join(DATA_DIR, "papers-latest.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_by_date(date_str):
    path = os.path.join(DATA_DIR, f"papers-{date_str}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_dates():
    pattern = os.path.join(DATA_DIR, "papers-????-??-??.json")
    files = sorted(glob.glob(pattern), reverse=True)
    return [os.path.basename(f).replace("papers-", "").replace(".json", "") for f in files]