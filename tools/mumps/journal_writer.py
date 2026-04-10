#!/usr/bin/env python3
"""Append-only journal writer. Dual-writes to project journal and per-ticket scratch log."""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

JOURNAL_PATH = Path("logs/luffy-journal.jsonl")


def append_event(path: Path, event: dict) -> None:
    """Append one JSON line. Never overwrites existing content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def write_journal(ticket_id: str, event_type: str, payload: dict) -> dict:
    """Write to both project journal and ticket scratch log."""
    timestamp = datetime.now(timezone.utc).isoformat()
    event = {
        "ticket_id": ticket_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "payload": payload,
    }
    append_event(JOURNAL_PATH, event)
    scratch_path = Path(f"logs/scratch-{ticket_id}.jsonl")
    append_event(scratch_path, event)
    return event


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", default="TEST-T00")
    parser.add_argument("--event", default="REASONING")
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        # Verify append-only behavior
        test_ticket = "BOOT-T02-test"
        e1 = write_journal(test_ticket, "REASONING", {"msg": "first"})
        e2 = write_journal(test_ticket, "VERIFY", {"msg": "second"})
        scratch = Path(f"logs/scratch-{test_ticket}.jsonl")
        lines = scratch.read_text().strip().splitlines()
        result = {
            "journal_append_ok": JOURNAL_PATH.exists(),
            "scratch_append_ok": scratch.exists(),
            "no_overwrite": len(lines) == 2,
            "line_count": len(lines),
        }
        print(json.dumps(result, indent=2))
    else:
        payload = json.loads(args.payload)
        event = write_journal(args.ticket, args.event, payload)
        print(json.dumps(event, indent=2))
