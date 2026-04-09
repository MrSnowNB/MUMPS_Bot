#!/usr/bin/env python3
"""
query_stack.py — Rook's filesystem query engine.

Used by Rook to answer natural-language QUERY intents without
entering the execution loop. All queries are read-only.
All query responses are logged to luffy-journal.jsonl (QUERY_RESPONSE event).

Usage (Rook calls this via exec_python tool):
    python scripts/query_stack.py --query "check the stack"
    python scripts/query_stack.py --query "how many open tickets"
    python scripts/query_stack.py --query "what failed"
    python scripts/query_stack.py --query "show dag"
    python scripts/query_stack.py --query "status"
"""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
TICKET_DIRS = {
    "open":        ROOT / "tickets" / "open",
    "in_progress": ROOT / "tickets" / "in_progress",
    "closed":      ROOT / "tickets" / "closed",
    "failed":      ROOT / "tickets" / "failed",
}
JOURNAL = ROOT / "logs" / "luffy-journal.jsonl"
SESSION_FILE = ROOT / "logs" / ".session"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def session_id() -> str:
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    return "unbound-" + str(uuid.uuid4())[:8]


def append_journal(event: dict):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a") as f:
        f.write(json.dumps(event) + "\n")


def count_dir(d: Path) -> int:
    if not d.exists():
        return 0
    return len([f for f in d.iterdir() if f.suffix == ".yaml"])


def ticket_ids(d: Path) -> list:
    if not d.exists():
        return []
    return sorted(f.stem for f in d.iterdir() if f.suffix == ".yaml")


def query_check_stack() -> str:
    lines = ["## Stack Status"]
    total = 0
    for name, d in TICKET_DIRS.items():
        n = count_dir(d)
        total += n
        ids = ticket_ids(d)
        lines.append(f"- **{name}**: {n}" + (f" ({', '.join(ids)})" if ids else ""))
    lines.append(f"\n**Total tickets**: {total}")
    return "\n".join(lines)


def query_open_count() -> str:
    n = count_dir(TICKET_DIRS["open"])
    ids = ticket_ids(TICKET_DIRS["open"])
    return f"{n} open ticket(s): {', '.join(ids) if ids else 'none'}"


def query_closed_count() -> str:
    n = count_dir(TICKET_DIRS["closed"])
    return f"{n} closed ticket(s)."


def query_failed() -> str:
    ids = ticket_ids(TICKET_DIRS["failed"])
    issue = ROOT / "ISSUE.md"
    lines = [f"Failed tickets: {', '.join(ids) if ids else 'none'}"]
    if issue.exists():
        lines.append("\n**Current ISSUE.md:**")
        lines.append(issue.read_text()[:800])
    return "\n".join(lines)


def query_dag() -> str:
    import yaml
    lines = ["## Ticket DAG"]
    for name in ["open", "in_progress", "closed", "failed"]:
        d = TICKET_DIRS[name]
        for f in sorted(d.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text())
                tid = data.get("id", f.stem)
                deps = data.get("depends_on", [])
                status = name.upper()
                lines.append(f"- `{tid}` [{status}] deps={deps or '[]'}")
            except Exception:
                lines.append(f"- `{f.stem}` [PARSE ERROR]")
    return "\n".join(lines)


def query_status() -> str:
    lines = ["## Rook Status"]
    for name, d in TICKET_DIRS.items():
        lines.append(f"  {name}: {count_dir(d)}")
    # last 5 journal events
    if JOURNAL.exists():
        events = JOURNAL.read_text().strip().splitlines()[-5:]
        lines.append("\n**Last 5 journal events:**")
        for e in events:
            try:
                j = json.loads(e)
                lines.append(f"  {j.get('ts','')} {j.get('event','')} {j.get('ticket','')}")
            except Exception:
                lines.append(f"  {e[:80]}")
    return "\n".join(lines)


QUERY_MAP = {
    "check the stack":        query_check_stack,
    "check stack":            query_check_stack,
    "stack":                  query_check_stack,
    "open":                   query_open_count,
    "how many open":          query_open_count,
    "how many open tickets":  query_open_count,
    "closed":                 query_closed_count,
    "how many closed":        query_closed_count,
    "how many closed tickets": query_closed_count,
    "failed":                 query_failed,
    "what failed":            query_failed,
    "show dag":               query_dag,
    "dag":                    query_dag,
    "status":                 query_status,
}


def dispatch(query: str) -> str:
    q = query.lower().strip().rstrip("?")
    for key, fn in QUERY_MAP.items():
        if key in q:
            return fn()
    return f"Unknown query: '{query}'. Try: check the stack, how many open, what failed, show dag, status."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    result = dispatch(args.query)
    print(result)

    # Log query to journal
    append_journal({
        "ts": now_iso(),
        "session": session_id(),
        "executor": "unspecified",
        "event": "QUERY_RESPONSE",
        "query_text": args.query,
        "response_summary": result.splitlines()[0][:120] if result else "empty",
    })


if __name__ == "__main__":
    main()
