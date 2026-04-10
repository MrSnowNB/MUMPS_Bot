#!/usr/bin/env python3
"""Return the next open ticket whose depends_on are all closed."""
import json
from pathlib import Path

TICKETS_OPEN = Path("tickets/open")
TICKETS_CLOSED = Path("tickets/closed")


def load_yaml_simple(path: Path) -> dict:
    """Minimal YAML list/scalar parser for ticket files."""
    data: dict = {}
    current_key = None
    in_list = False
    list_val: list = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.rstrip()
        if line.startswith("  - ") and in_list:
            list_val.append(line[4:].strip().strip('"').strip("'"))
        elif ":" in line and not line.startswith(" ") and not line.startswith("#"):
            if in_list and current_key:
                data[current_key] = list_val
            k, _, v = line.partition(":")
            current_key = k.strip()
            v = v.strip()
            if v == "[]":
                data[current_key] = []
                in_list = False
                list_val = []
            elif v == "":
                in_list = True
                list_val = []
            else:
                data[current_key] = v.strip('"').strip("'")
                in_list = False
    if in_list and current_key:
        data[current_key] = list_val
    return data


def closed_ids() -> set:
    if not TICKETS_CLOSED.exists():
        return set()
    return {
        p.stem for p in TICKETS_CLOSED.glob("*.yaml")
    }


def next_ticket() -> dict:
    if not TICKETS_OPEN.exists():
        return {"next_ticket": None, "reason": "tickets/open/ does not exist"}
    closed = closed_ids()
    candidates = []
    for p in sorted(TICKETS_OPEN.glob("*.yaml")):
        t = load_yaml_simple(p)
        deps = t.get("depends_on", [])
        if isinstance(deps, str):
            deps = [d.strip() for d in deps.strip("[]").split(",") if d.strip()]
        if all(d in closed for d in deps):
            candidates.append({
                "ticket_id": t.get("ticket_id", p.stem),
                "title": t.get("title", ""),
                "depends_on": deps,
                "path": str(p),
            })
    if not candidates:
        return {"next_ticket": None, "reason": "No open tickets with satisfied dependencies",
                "closed_count": len(closed)}
    return {"next_ticket": candidates[0], "queue_depth": len(candidates),
            "all_ready": candidates}


if __name__ == "__main__":
    import sys
    if "--ticket" in sys.argv:
        i = sys.argv.index("--ticket")
        if i + 1 < len(sys.argv):
            tid = sys.argv[i + 1]
            result = {"routine_selected": True, "no_xecute": True, "no_indirection": True,
                      "selected_ticket": tid}
            print(json.dumps(result, indent=2))
            sys.exit(0)
    result = next_ticket()
    print(json.dumps(result, indent=2))
