#!/usr/bin/env python3
"""
Append a JSON object to a JSONL file (creates file if missing).
Usage: python scripts/append_jsonl.py logs/luffy-journal.jsonl '{...}'
"""
import json, sys, pathlib, datetime

def append_jsonl(path: str, entry_str: str):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = json.loads(entry_str)
    if "ts" not in entry:
        entry["ts"] = datetime.datetime.utcnow().isoformat()
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    append_jsonl(sys.argv[1], sys.argv[2])
