"""Tool: summarize_routine — synthesize per-entry-point summary from prerequisite JSONs.

Usage:
    python tools/mumps/summarize_routine.py <filepath.m> \
        --entries output/<R>-entry-points.json \
        --globals output/<R>-globals.json \
        --calls   output/<R>-calls.json

Output:
    output/<ROUTINE>-summary.json  — JSON dict with keys:
        routine_name, entry_point_count, global_count, call_count, complexity_flags,
        entry_points (list)

Dependency: standard library only (no tree-sitter needed here)
"""
import argparse
import json
import sys
from pathlib import Path

COMPLEXITY_PATTERNS = {
    "xecute":    ("XECUTE dynamic execution", "high"),
    "@ ":        ("@ indirection",            "high"),
    "^die":      ("FileMan DIE call",          "medium"),
    "^rghllog":  ("HL7 audit log",             "medium"),
    " lock":     ("LOCK/UNLOCK",               "medium"),
    "$order":    ("$ORDER traversal",          "medium"),
}


def summarize_routine(filepath: str, entries_path: str,
                      globals_path: str, calls_path: str) -> dict:
    stem = Path(filepath).stem
    entries   = json.loads(Path(entries_path).read_text())
    gmap      = json.loads(Path(globals_path).read_text())
    calls     = json.loads(Path(calls_path).read_text())
    src_lines = Path(filepath).read_text(errors="replace").splitlines()

    complexity_flags = []
    ep_summaries = []

    for ep in entries:
        label = ep["label"]
        start, end = ep["line_start"] - 1, ep["line_end"]
        snippet = "\n".join(src_lines[start:end]).lower()
        complexity, notes = "low", []
        for pat, (note, level) in COMPLEXITY_PATTERNS.items():
            if pat in snippet:
                notes.append(note)
                if level == "high":
                    complexity = "high"
                elif level == "medium" and complexity != "high":
                    complexity = "medium"
                if note not in complexity_flags:
                    complexity_flags.append(note)

        ep_summaries.append({
            "label":              label,
            "args":               ep.get("args", []),
            "line_start":         ep["line_start"],
            "line_count":         ep["line_count"],
            "globals_read":       sorted({
                g for g, d in gmap.items()
                for r in d.get("reads", []) if r.get("label") == label
            }),
            "globals_written":    sorted({
                g for g, d in gmap.items()
                for w in d.get("writes", []) if w.get("label") == label
            }),
            "external_calls":     [c for c in calls if c.get("caller") == label],
            "translation_complexity": complexity,
            "complexity_notes":   notes,
        })

    return {
        "routine_name":     stem,
        "entry_point_count": len(entries),
        "global_count":     len(gmap),
        "call_count":       len(calls),
        "complexity_flags": complexity_flags,
        "entry_points":     ep_summaries,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("filepath")
    ap.add_argument("--entries",  required=True)
    ap.add_argument("--globals",  required=True)
    ap.add_argument("--calls",    required=True)
    args = ap.parse_args()

    result = summarize_routine(
        args.filepath, args.entries, args.globals, args.calls
    )
    stem = Path(args.filepath).stem
    out_path = Path("output") / f"{stem}-summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {result['entry_point_count']} entry points -> {out_path}")
