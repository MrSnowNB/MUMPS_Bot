#!/usr/bin/env python3
"""Return the next open ticket whose depends_on are all closed."""
import json
from pathlib import Path

TICKETS_OPEN   = Path("tickets/open")
TICKETS_CLOSED = Path("tickets/closed")


def parse_inline_list(v: str) -> list[str]:
    """Parse YAML inline list string e.g. '[BOOT-T01, BOOT-T02]' -> ['BOOT-T01','BOOT-T02'].
    Also handles bare comma-separated values without brackets.
    Returns [] for empty string, '[]', or '""'.
    """
    v = v.strip().strip('"').strip("'")
    if v in ("", "[]"):
        return []
    v = v.strip("[]")
    return [item.strip().strip('"').strip("'") for item in v.split(",") if item.strip()]


def load_yaml_simple(path: Path) -> dict:
    """Minimal YAML parser for ticket files.
    Handles:
      - Scalar values:          key: value
      - Empty inline lists:     key: []
      - Populated inline lists: key: [A, B, C]
      - Block lists:            key:\n  - A\n  - B
    """
    data: dict = {}
    current_key: str | None = None
    in_block_list: bool = False
    block_list: list = []

    for raw_line in path.read_text().splitlines():
        line = raw_line.rstrip()

        # Block list item
        if in_block_list and line.startswith("  - "):
            block_list.append(line[4:].strip().strip('"').strip("'"))
            continue

        # New top-level key — flush any pending block list
        if ":" in line and not line.startswith(" ") and not line.startswith("#"):
            if in_block_list and current_key is not None:
                data[current_key] = block_list
                in_block_list = False
                block_list = []

            k, _, v = line.partition(":")
            current_key = k.strip()
            v = v.strip()

            if v == "":
                # Could be start of block list — defer until we see next line
                in_block_list = True
                block_list = []
            elif v.startswith("["):
                # Inline list — always parse immediately
                data[current_key] = parse_inline_list(v)
                in_block_list = False
            else:
                data[current_key] = v.strip('"').strip("'")
                in_block_list = False

    # Flush trailing block list
    if in_block_list and current_key is not None:
        data[current_key] = block_list

    return data


def closed_ids() -> set[str]:
    if not TICKETS_CLOSED.exists():
        return set()
    return {p.stem for p in TICKETS_CLOSED.glob("*.yaml")}


def next_ticket() -> dict:
    if not TICKETS_OPEN.exists():
        return {"next_ticket": None, "reason": "tickets/open/ does not exist"}

    closed = closed_ids()
    candidates = []

    for p in sorted(TICKETS_OPEN.glob("*.yaml")):
        if p.name == ".gitkeep":
            continue
        t = load_yaml_simple(p)
        deps = t.get("depends_on", [])
        # Normalise: scalar string fallback (should not happen after parser fix)
        if isinstance(deps, str):
            deps = parse_inline_list(deps)

        if all(d in closed for d in deps):
            candidates.append({
                "ticket_id": t.get("ticket_id", p.stem),
                "title":     t.get("title", ""),
                "depends_on": deps,          # <-- actual list, never []
                "path":      str(p),
            })

    if not candidates:
        return {
            "next_ticket": None,
            "reason": "No open tickets with satisfied dependencies",
            "closed_count": len(closed),
        }

    return {
        "next_ticket": candidates[0],
        "queue_depth": len(candidates),
        "all_ready": candidates,
    }


if __name__ == "__main__":
    import sys
    result = next_ticket()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("next_ticket") is not None else 1)
