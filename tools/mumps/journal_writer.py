#!/usr/bin/env python3
"""Append-only journal writer. Dual-writes to project journal and per-ticket scratch log."""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

JOURNAL_PATH = Path("logs/luffy-journal.jsonl")
SESSION_FILE = Path("logs/.session")


def get_session_id() -> str:
    """Get or create session UUID."""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    session_id = str(uuid4())
    SESSION_FILE.write_text(session_id + "\n")
    return session_id


def get_executor_tag() -> str:
    """Get executor tag from settings.yaml."""
    settings_path = Path("settings.yaml")
    if settings_path.exists():
        import yaml
        with open(settings_path, "r") as f:
            settings = yaml.safe_load(f)
        return settings.get("model_tag", "unspecified")
    return "unspecified"


def append_event(path: Path, event: dict) -> None:
    """Append one JSON line. Never overwrites existing content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def write_journal(ticket_id: str, event_type: str, payload: dict) -> dict:
    """Write to both project journal and ticket scratch log."""
    timestamp = datetime.now(timezone.utc).isoformat()
    session_id = get_session_id()
    executor_tag = get_executor_tag()
    
    event = {
        "ts": timestamp,
        "session": session_id,
        "executor": executor_tag,
        "event": event_type,
        "ticket": ticket_id,
        "payload": payload,
    }
    
    append_event(JOURNAL_PATH, event)
    scratch_path = Path(f"logs/scratch-{ticket_id}.jsonl")
    append_event(scratch_path, event)
    
    return event


def verify_journal_integrity(journal_path: Path) -> dict:
    """Verify journal append-only integrity."""
    if not journal_path.exists():
        return {"exists": False, "valid": True, "line_count": 0}
    
    lines = journal_path.read_text(encoding="utf-8").strip().splitlines()
    result = {"exists": True, "line_count": len(lines), "valid": True, "errors": []}
    
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            required_fields = ["ts", "session", "executor", "event"]
            for field in required_fields:
                if field not in entry:
                    result["valid"] = False
                    result["errors"].append(f"Line {i+1}: missing field '{field}'")
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"Line {i+1}: invalid JSON - {str(e)}")
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", default="TEST-T00")
    parser.add_argument("--event", default="REASONING")
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        # Clean up test files first
        test_ticket = "BOOT-T02-test"
        scratch_path = Path(f"logs/scratch-{test_ticket}.jsonl")
        if scratch_path.exists():
            scratch_path.unlink()
        
        # Test append-only behavior
        e1 = write_journal(test_ticket, "REASONING", {"msg": "first"})
        e2 = write_journal(test_ticket, "VERIFY", {"msg": "second"})
        
        # Verify journal integrity
        journal_result = verify_journal_integrity(JOURNAL_PATH)
        scratch = Path(f"logs/scratch-{test_ticket}.jsonl")
        scratch_lines = scratch.read_text().strip().splitlines() if scratch.exists() else []
        
        result = {
            "journal_append_ok": journal_result["exists"],
            "scratch_append_ok": scratch.exists(),
            "no_overwrite": len(scratch_lines) == 2,
            "line_count": len(scratch_lines),
            "journal_valid": journal_result["valid"],
            "journal_lines": journal_result["line_count"],
            "scratch_lines": len(scratch_lines),
        }
        print(json.dumps(result, indent=2))
    else:
        payload = json.loads(args.payload)
        event = write_journal(args.ticket, args.event, payload)
        print(json.dumps(event, indent=2))