"""Tool: emit_python_stub — generate typed Python stubs from <ROUTINE>-summary.json.

Usage:
    python tools/mumps/emit_python_stub.py <summary.json>

Output:
    output/<ROUTINE>-stub.py  — typed Python stubs with docstrings and TODO markers

Dependency: standard library only
"""
import json
import sys
from pathlib import Path


def emit_python_stub(summary_path: str) -> str:
    summary = json.loads(Path(summary_path).read_text())
    routine = summary["routine_name"]
    lines = []
    lines += [
        f'"""',
        f"Guardian stub: {routine}",
        f"Stage: STUB — not yet verified",
        f'"""',
        "from __future__ import annotations",
        "from typing import Union",
        "",
    ]
    for ep in summary["entry_points"]:
        label = ep["label"]
        args  = ep.get("args", [])
        sig   = ", ".join(f"{a}: str" for a in args) if args else ""
        lines += [
            "",
            f"def {label.lower()}({sig}) -> Union[str, int]:",
            f'    """',
            f"    MUMPS: {label}({', '.join(args)})",
            f"    Lines: {ep['line_start']}–{ep['line_start'] + ep['line_count'] - 1}",
        ]
        if ep.get("globals_read"):
            lines.append(f"    Globals read:    {', '.join(ep['globals_read'])}")
        if ep.get("globals_written"):
            lines.append(f"    Globals written: {', '.join(ep['globals_written'])}")
        if ep.get("external_calls"):
            ext = [c["callee"] for c in ep["external_calls"]]
            lines.append(f"    External calls:  {', '.join(ext)}")
        if ep.get("complexity_notes"):
            lines.append(
                f"    Complexity [{ep['translation_complexity']}]: "
                f"{'; '.join(ep['complexity_notes'])}"
            )
        lines.append(f'    Returns: value or "-1^<error>" on failure')
        lines.append(f'    """')
        if ep.get("translation_complexity") == "high":
            lines.append(f"    # TODO(HIGH): {'; '.join(ep.get('complexity_notes', []))}")
            lines.append(f"    raise NotImplementedError('{label}: high-complexity translation required')")
        else:
            lines.append(f"    # TODO: implement — see MUMPS line {ep['line_start']}")
            lines.append(f"    raise NotImplementedError('{label}')")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: emit_python_stub.py <summary.json>", file=sys.stderr)
        sys.exit(1)
    result = emit_python_stub(sys.argv[1])
    stem = Path(sys.argv[1]).stem.replace("-summary", "")
    out_path = Path("output") / f"{stem}-stub.py"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result)
    print(f"OK: stubs written to {out_path}")
