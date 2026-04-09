"""Tool: list_entry_points — extract all labeled entry points from a MUMPS routine.

Usage:
    python tools/mumps/list_entry_points.py <filepath.m>

Output:
    output/<ROUTINE>-entry-points.json  — JSON list, each item: label, line_start, line_end, args

Dependency: pip install tree-sitter-languages>=1.10.2
"""
import json
import sys
from pathlib import Path


def list_entry_points(filepath: str) -> list:
    from tree_sitter_languages import get_parser
    parser = get_parser("mumps")
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    entries = []

    def walk(node):
        if node.type == "routine_definition":
            label_node = next(
                (c for c in node.children if c.type == "label"), None
            )
            if label_node:
                label = label_node.text.decode("utf-8", errors="replace").strip()
                args = [
                    c.text.decode("utf-8", errors="replace").strip()
                    for c in node.children
                    if c.type in ("function_name", "local_variable")
                ]
                entries.append({
                    "label": label,
                    "args": args,
                    "line_start": node.start_point[0] + 1,
                    "line_end": node.end_point[0] + 1,
                    "line_count": node.end_point[0] - node.start_point[0] + 1,
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return entries


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: list_entry_points.py <filepath.m>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    result = list_entry_points(filepath)
    out_path = Path("output") / f"{Path(filepath).stem}-entry-points.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} entry points -> {out_path}")
