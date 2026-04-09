#!/usr/bin/env python3
"""Reset all tickets to OPEN state and append HARNESS_RESET to log."""
import os
import shutil
import json
from datetime import datetime, timezone

DIRS = ["tickets/in_progress", "tickets/closed", "tickets/failed"]
OPEN = "tickets/open"
LOG = "logs/luffy-journal.jsonl"

def main():
    moved = []
    for d in DIRS:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".yaml"):
                src = os.path.join(d, fn)
                dst = os.path.join(OPEN, fn)
                shutil.move(src, dst)
                moved.append(fn)
                print(f"  moved {src} → {dst}")

    reset_event = {
        "event": "HARNESS_RESET",
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "operator": "reset_tickets.py",
        "tickets_moved_to_open": moved,
        "note": f"Reset {len(moved)} tickets to OPEN."
    }
    os.makedirs("logs", exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(reset_event) + "\n")

    print(f"\nReset complete. {len(moved)} tickets moved to OPEN.")
    print(f"HARNESS_RESET event appended to {LOG}.")

if __name__ == "__main__":
    main()
