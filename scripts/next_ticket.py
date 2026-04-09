#!/usr/bin/env python3
"""Show which tickets in open/ are ready to run (all deps in closed/)."""
import os
import yaml
import sys

OPEN = "tickets/open"
CLOSED = "tickets/closed"

def closed_ids():
    ids = set()
    if os.path.isdir(CLOSED):
        for fn in os.listdir(CLOSED):
            if fn.endswith(".yaml"):
                ids.add(fn.replace(".yaml", ""))
    return ids

def main():
    closed = closed_ids()
    ready = []
    blocked = []

    for fn in sorted(os.listdir(OPEN)):
        if not fn.endswith(".yaml"):
            continue
        with open(os.path.join(OPEN, fn)) as f:
            t = yaml.safe_load(f)
        deps = t.get("depends_on", []) or []
        missing = [d for d in deps if d not in closed]
        if not missing:
            ready.append((t["id"], t.get("priority", 5), t.get("title", "")))
        else:
            blocked.append((t["id"], missing))

    ready.sort(key=lambda x: x[1])

    print("=== READY TO RUN ===")
    for tid, pri, title in ready:
        print(f"  [{pri}] {tid}: {title}")

    if blocked:
        print("\n=== WAITING ON DEPS ===")
        for tid, missing in blocked:
            print(f"  {tid} waiting for: {', '.join(missing)}")

if __name__ == "__main__":
    main()
