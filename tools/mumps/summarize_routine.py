"""
Tool: summarize_routine — synthesize per-entry-point summary from prerequisite JSONs
"""
import json, sys
from pathlib import Path

COMPLEXITY_PATTERNS = {
    "xecute": ("XECUTE dynamic execution", "high"),
    "@ ": ("@ indirection", "high"),
    "^die": ("FileMan DIE call", "medium"),
    "^rghllog": ("HL7 audit log", "medium"),
    " lock": ("LOCK/UNLOCK", "medium"),
    "$order": ("$ORDER traversal", "medium"),
}

def summarize_routine(filepath: str) -> dict:
    stem = Path(filepath).stem
    out_dir = Path("output") / stem
    entries = json.loads((out_dir / f"{stem}_entries.json").read_text())
    globals_map = json.loads((out_dir / f"{stem}_globals.json").read_text())
    calls = json.loads((out_dir / f"{stem}_calls.json").read_text())
    source_lines = Path(filepath).read_text(errors="replace").splitlines()
    summary = {"routine": stem, "entry_points": []}
    for ep in entries:
        label = ep["label"]
        start, end = ep["start_line"]-1, ep["end_line"]
        snippet = "\n".join(source_lines[start:end]).lower()
        complexity, notes = "low", []
        for pat, (note, level) in COMPLEXITY_PATTERNS.items():
            if pat in snippet:
                notes.append(note)
                if level == "high": complexity = "high"
                elif level == "medium" and complexity != "high": complexity = "medium"
        summary["entry_points"].append({
            "label": label, "args": ep["args"],
            "start_line": ep["start_line"], "line_count": ep["line_count"],
            "return_type": 'str  # "-1^error" or value',
            "globals_read": sorted({g for g, d in globals_map.items() for r in d["reads"] if r["label"]==label}),
            "globals_written": sorted({g for g, d in globals_map.items() for w in d["writes"] if w["label"]==label}),
            "external_calls": [c for c in calls if c["from_label"]==label],
            "translation_complexity": complexity, "complexity_notes": notes,
        })
    return summary

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = summarize_routine(filepath)
    out_path = Path("output") / Path(filepath).stem / f"{Path(filepath).stem}_summary.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result['entry_points'])} entry points → {out_path}")
