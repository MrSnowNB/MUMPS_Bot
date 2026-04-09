"""
Tool: emit_python_stub — generate typed Python stubs from summary JSON
"""
import json, sys
from pathlib import Path

def emit_python_stub(summary_path: str) -> str:
    summary = json.loads(Path(summary_path).read_text())
    routine = summary["routine"]
    L = []
    L += [f'"""\nGuardian stub: {routine}\nStage: STUB — not yet verified\n"""',
          "from __future__ import annotations", "from typing import Union", ""]
    for ep in summary["entry_points"]:
        label, args = ep["label"], ep["args"]
        sig = ", ".join(f"{a}: str" for a in args) if args else ""
        ret = "Union[str, int]"
        L += ["", f"def {label.lower()}({sig}) -> {ret}:"]
        L.append(f'    """')
        L.append(f"    MUMPS: {label}({', '.join(args)})")
        L.append(f"    Lines: {ep['start_line']}–{ep['start_line']+ep['line_count']-1}")
        if ep["globals_read"]:   L.append(f"    Globals read:    {', '.join(ep['globals_read'])}")
        if ep["globals_written"]: L.append(f"    Globals written: {', '.join(ep['globals_written'])}")
        if ep["external_calls"]:
            ext = [f"{c['to_label']}^{c['to_routine']}" for c in ep["external_calls"]]
            L.append(f"    External calls:  {', '.join(ext)}")
        if ep["complexity_notes"]: L.append(f"    Complexity [{ep['translation_complexity']}]: {'; '.join(ep['complexity_notes'])}")
        L.append(f'    Returns: value or "-1^<error>" on failure\n    """')
        if ep["translation_complexity"] == "high":
            L.append(f"    # TODO(HIGH): {'; '.join(ep['complexity_notes'])}")
            L.append(f"    raise NotImplementedError('{label}: high-complexity')")
        else:
            L.append(f"    # TODO: implement — see MUMPS line {ep['start_line']}")
            L.append(f"    raise NotImplementedError('{label}')")
    return "\n".join(L)

if __name__ == "__main__":
    summary_path = sys.argv[1]
    result = emit_python_stub(summary_path)
    stem = Path(summary_path).stem.replace("_summary", "")
    out_path = Path("output") / stem / "stubs.py"
    out_path.write_text(result)
    print(f"OK: stubs written to {out_path}")
