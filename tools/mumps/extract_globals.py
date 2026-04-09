"""Tool: extract_globals — map global array read/write patterns per entry point.

Usage:
    python tools/mumps/extract_globals.py <filepath.m>

Output:
    output/<ROUTINE>-globals.json  — JSON dict keyed by global name,
                                     each value: {reads: [...], writes: [...]}

Dependency: pip install tree-sitter-languages>=1.10.2
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def extract_globals(filepath: str) -> dict:
    from tree_sitter_languages import get_parser
    parser = get_parser("mumps")
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    gmap = defaultdict(lambda: {"reads": [], "writes": []})
    current_label = ["ROUTINE_LEVEL"]

    def walk(node):
        if node.type == "routine_definition":
            lbl = next((c for c in node.children if c.type == "label"), None)
            if lbl:
                current_label[0] = lbl.text.decode("utf-8", errors="replace").strip()
        if node.type == "global_array":
            text = node.text.decode("utf-8", errors="replace").strip()
            base = text.split("(")[0] if "(" in text else text
            is_write = (
                node.parent
                and node.parent.type == "assignment"
                and any(
                    c == node
                    for c in node.parent.children
                    if c.type in ("global_array", "_multiple_assignment_identifiers")
                )
            )
            entry = {"pattern": text, "line": node.start_point[0] + 1, "label": current_label[0]}
            if is_write:
                gmap[base]["writes"].append(entry)
            else:
                gmap[base]["reads"].append(entry)
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return dict(gmap)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_globals.py <filepath.m>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    result = extract_globals(filepath)
    out_path = Path("output") / f"{Path(filepath).stem}-globals.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} globals -> {out_path}")
