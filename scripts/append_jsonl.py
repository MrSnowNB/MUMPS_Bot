#!/usr/bin/env python3
"""
Append a JSON event to logs/luffy-journal.jsonl.
Usage: python scripts/append_jsonl.py '{"event":"...","ticket_id":"..."}'

Always writes to the authoritative log path. Does NOT accept an arbitrary
path argument to prevent accidental writes to stale journal files.
"""
import json
import sys
import pathlib
import datetime

LOG_PATH = pathlib.Path("logs/luffy-journal.jsonl")

def append_event(entry_str: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = json.loads(entry_str)
    # Always stamp with UTC ISO-8601 if caller omitted ts
    if "ts" not in entry:
        entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    # Reject writes if event field is missing
    if "event" not in entry:
        print("ERROR: JSON entry must contain an 'event' field.", file=sys.stderr)
        sys.exit(1)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Appended event '{entry['event']}' to {LOG_PATH}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} '{{\"event\":\"...\"}}'")
        sys.exit(1)
    append_event(sys.argv[1])
