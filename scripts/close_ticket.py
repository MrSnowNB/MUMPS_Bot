#!/usr/bin/env python3
"""Ticket close enforcer — verifies REASONING, VERIFY, artifact, and gate before close."""
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

TICKETS_DIR = Path("tickets")
LOGS_DIR = Path("logs")


def load_ticket(ticket_id: str) -> dict | None:
    for state in ["open", "in_progress"]:
        p = TICKETS_DIR / state / f"{ticket_id}.yaml"
        if p.exists():
            try:
                import yaml  # type: ignore
                return yaml.safe_load(p.read_text())
            except ImportError:
                # Minimal YAML key:value parser fallback
                data = {}
                for line in p.read_text().splitlines():
                    if ":" in line and not line.startswith(" ") and not line.startswith("#"):
                        k, _, v = line.partition(":")
                        data[k.strip()] = v.strip()
                return data
    return None


def check_scratch(ticket_id: str) -> dict:
    scratch = LOGS_DIR / f"scratch-{ticket_id}.jsonl"
    if not scratch.exists():
        return {"reasoning": False, "verify": False}
    events = [json.loads(l) for l in scratch.read_text().strip().splitlines() if l.strip()]
    types = {e.get("event_type", "") for e in events}
    return {
        "reasoning": "REASONING" in types,
        "verify": "VERIFY" in types,
    }


def close_ticket(ticket_id: str, dry_run: bool = False) -> dict:
    ticket = load_ticket(ticket_id)
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found in open/ or in_progress/"}

    result_path = Path(ticket.get("result_path", ""))
    scratch = check_scratch(ticket_id)
    artifact_ok = result_path.exists() if str(result_path) else True
    reasoning_ok = scratch["reasoning"]
    verify_ok = scratch["verify"]
    all_ok = artifact_ok and reasoning_ok and verify_ok

    verdict = {
        "ticket_id": ticket_id,
        "artifact_exists": artifact_ok,
        "reasoning_present": reasoning_ok,
        "verify_present": verify_ok,
        "close_enforced": True,
        "reasoning_required": True,
        "verify_required": True,
        "can_close": all_ok,
        "dry_run": dry_run,
    }

    if not dry_run and all_ok:
        # Move ticket file to closed/
        for state in ["open", "in_progress"]:
            src = TICKETS_DIR / state / f"{ticket_id}.yaml"
            if src.exists():
                dst = TICKETS_DIR / "closed" / f"{ticket_id}.yaml"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                verdict["moved_to"] = str(dst)
    elif not dry_run and not all_ok:
        for state in ["open", "in_progress"]:
            src = TICKETS_DIR / state / f"{ticket_id}.yaml"
            if src.exists():
                dst = TICKETS_DIR / "failed" / f"{ticket_id}.yaml"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                verdict["moved_to"] = str(dst)
    return verdict


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = close_ticket(args.ticket, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
