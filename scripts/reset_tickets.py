#!/usr/bin/env python3
"""
Reset all tickets to OPEN state.

Moves all .yaml files from tickets/in_progress/, tickets/closed/,
and tickets/failed/ back into tickets/open/, then appends a
HARNESS_RESET event to logs/luffy-journal.jsonl.

Does NOT touch logs/luffy-journal.jsonl.
Only logs/luffy-journal.jsonl is authoritative.

Usage: python scripts/reset_tickets.py
"""
import os
import shutil
import json
import yaml
from datetime import datetime, timezone

DIRS = ["tickets/in_progress", "tickets/closed", "tickets/failed"]
OPEN = "tickets/open"
LOG = "logs/luffy-journal.jsonl"  # single authoritative log

def main():
    moved = []
    for d in DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".yaml"):
                src = os.path.join(d, fn)
                dst = os.path.join(OPEN, fn)
                if os.path.exists(dst):
                    print(f"  SKIP (already in open): {fn}")
                    continue
                shutil.move(src, dst)
                moved.append(fn)
                print(f"  moved  {src} -> {dst}")

    # Zero out attempts on all tickets in open/
    for fn in sorted(os.listdir(OPEN)):
        if not fn.endswith(".yaml"):
            continue
        fpath = os.path.join(OPEN, fn)
        with open(fpath) as f:
            raw = f.read()
        # Handle frontmatter-delimited YAML (--- ... ---)
        docs = list(yaml.safe_load_all(raw))
        ticket = None
        for doc in docs:
            if isinstance(doc, dict):
                ticket = doc
                break
        if ticket:
            ticket["attempts"] = 0
            ticket["status"] = "open"
            with open(fpath, "w") as f:
                f.write("---\n")
                yaml.dump(ticket, f, default_flow_style=False)
                f.write("---\n")
            print(f"  zeroed attempts: {fn}")

    reset_event = {
        "event": "HARNESS_RESET",
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "operator": "reset_tickets.py",
        "tickets_moved_to_open": moved,
        "note": f"Reset {len(moved)} ticket(s) to OPEN. Log: {LOG}"
    }
    os.makedirs("logs", exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(reset_event) + "\n")

    print(f"\nDone. {len(moved)} ticket(s) reset to OPEN.")
    print(f"HARNESS_RESET appended to {LOG}.")

if __name__ == "__main__":
    main()
