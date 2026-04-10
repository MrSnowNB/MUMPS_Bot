#!/usr/bin/env python3
"""Verify required repo skeleton directories exist and are writable."""
import json
import os
from pathlib import Path

REQUIRED_DIRS = [
    "routines",
    "tickets/open",
    "tickets/in_progress",
    "tickets/closed",
    "tickets/failed",
    "logs",
    "output",
    "tools/mumps",
    "scripts",
]


def check_skeleton() -> dict:
    results = {}
    for d in REQUIRED_DIRS:
        p = Path(d)
        exists = p.exists() and p.is_dir()
        writable = os.access(p, os.W_OK) if exists else False
        results[d] = {"exists": exists, "writable": writable}
        if not exists:
            p.mkdir(parents=True, exist_ok=True)
            gk = p / ".gitkeep"
            if not gk.exists():
                gk.touch()
            results[d] = {"exists": True, "writable": True, "created": True}
    all_ok = all(v["exists"] and v["writable"] for v in results.values())
    return {"all_dirs_exist": all_ok, "dirs": results}


if __name__ == "__main__":
    result = check_skeleton()
    import sys
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        result["file_exists"] = p.exists()
        result["path"] = str(p)
    print(json.dumps(result, indent=2))
