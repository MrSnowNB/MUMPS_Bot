#!/usr/bin/env python3
"""
scheduler.py — DAG-aware ticket picker.

Usage (standalone):
    python agent/scheduler.py           # print next ready ticket
    python agent/scheduler.py --all     # print full ready queue
    python agent/scheduler.py --status  # print counts per state
"""

from pathlib import Path
import yaml

ROOT = Path(__file__).parent.parent


def load_tickets(directory: Path) -> list[dict]:
    tickets = []
    for p in sorted(directory.glob("*.yaml")):
        raw = p.read_text().strip()
        lines = raw.splitlines()
        if lines and lines[0] == "---":
            try:
                end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
                front = "\n".join(lines[1:end])
                data = yaml.safe_load(front)
                if isinstance(data, dict):
                    data["_path"] = p
                    tickets.append(data)
            except StopIteration:
                pass
    return tickets


def closed_ids() -> set:
    closed_dir = ROOT / "tickets" / "closed"
    return {p.stem for p in closed_dir.glob("*.yaml")}


def ready_tickets() -> list[dict]:
    open_dir = ROOT / "tickets" / "open"
    done = closed_ids()
    ready = []
    for t in load_tickets(open_dir):
        deps = t.get("depends_on") or []
        if t.get("status") == "open" and all(d in done for d in deps):
            ready.append(t)
    return ready


def status_counts() -> dict:
    counts = {}
    for state in ["open", "in_progress", "closed", "failed"]:
        d = ROOT / "tickets" / state
        counts[state] = len(list(d.glob("*.yaml"))) if d.exists() else 0
    return counts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        for state, count in status_counts().items():
            print(f"{state:<15} {count}")
    elif args.all:
        for t in ready_tickets():
            print(f"{t['id']:<12} {t.get('title', '')}")
    else:
        ready = ready_tickets()
        if ready:
            t = ready[0]
            print(f"{t['id']} — {t.get('title', '')}")
        else:
            print("No ready tickets.")
