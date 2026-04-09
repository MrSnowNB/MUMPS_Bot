"""Tool: list_entry_points — extract all labeled entry points from MUMPS routine."""
import json, sys
from pathlib import Path

def list_entry_points(filepath: str) -> list:
    from tree_sitter import Language, Parser
    grammar_path = Path(__file__).parent / "build" / "mumps.so"
    MUMPS_LANGUAGE = Language(str(grammar_path), "mumps")
    parser = Parser(); parser.set_language(MUMPS_LANGUAGE)
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    entries = []

    def walk(node):
        if node.type == "routine_definition":
            label_node = next((c for c in node.children if c.type == "label"), None)
            if label_node:
                label = label_node.text.decode("utf-8", errors="replace").strip()
                args = [c.text.decode("utf-8", errors="replace").strip() for c in node.children
                        if c.type in ("function_name", "local_variable")]
                entries.append({"label": label, "args": args,
                    "start_line": node.start_point[0]+1, "end_line": node.end_point[0]+1,
                    "line_count": node.end_point[0]-node.start_point[0]+1})
        for child in node.children: walk(child)

    walk(tree.root_node)
    return entries

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = list_entry_points(filepath)
    out_path = Path("output") / Path(filepath).stem / f"{Path(filepath).stem}_entries.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} entry points → {out_path}")
