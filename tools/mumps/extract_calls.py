"""Tool: extract_calls — build cross-routine call graph from MUMPS routine.

Usage:
    python tools/mumps/extract_calls.py <filepath.m>

Output:
    output/<ROUTINE>-calls.json  — JSON list, each item: caller, callee, call_type, line

Dependency: pip install tree-sitter-languages>=1.10.2
"""
import json
import sys
from pathlib import Path


def extract_calls(filepath: str) -> list:
    from tree_sitter_languages import get_parser
    parser = get_parser("mumps")
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    calls = []
    current_label = ["ROUTINE_LEVEL"]

    def parse_ref(text):
        text = text.strip().lstrip("$")
        if "^" in text:
            parts = text.split("^")
            return (
                parts[0].split("(")[0] if parts[0] else "",
                parts[1].split("(")[0] if len(parts) > 1 else "",
            )
        return text.split("(")[0], ""

    def walk(node):
        if node.type == "routine_definition":
            lbl = next((c for c in node.children if c.type == "label"), None)
            if lbl:
                current_label[0] = lbl.text.decode("utf-8", errors="replace").strip()
        if node.type == "routine_call":
            text = node.text.decode("utf-8", errors="replace").strip()
            to_label, to_routine = parse_ref(text)
            if to_routine:
                call_type = "extrinsic_function" if "$$" in text else "do"
                if node.parent and node.parent.type == "goto_command":
                    call_type = "goto"
                calls.append({
                    "caller": current_label[0],
                    "callee": f"{to_label}^{to_routine}" if to_label else to_routine,
                    "call_type": call_type,
                    "line": node.start_point[0] + 1,
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return calls


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_calls.py <filepath.m>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    result = extract_calls(filepath)
    out_path = Path("output") / f"{Path(filepath).stem}-calls.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} calls -> {out_path}")
