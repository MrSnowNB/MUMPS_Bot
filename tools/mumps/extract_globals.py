"""Tool: extract_globals — map all global read/write patterns per entry point."""
import json, sys
from pathlib import Path
from collections import defaultdict

def extract_globals(filepath: str) -> dict:
    from tree_sitter import Language, Parser
    grammar_path = Path(__file__).parent / "build" / "mumps.so"
    MUMPS_LANGUAGE = Language(str(grammar_path), "mumps")
    parser = Parser(); parser.set_language(MUMPS_LANGUAGE)
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    gmap = defaultdict(lambda: {"reads":[], "writes":[], "routines":set()})
    current = ["ROUTINE_LEVEL"]

    def walk(node):
        if node.type == "routine_definition":
            lbl = next((c for c in node.children if c.type == "label"), None)
            if lbl: current[0] = lbl.text.decode("utf-8", errors="replace").strip()
        if node.type == "global_array":
            text = node.text.decode("utf-8", errors="replace").strip()
            base = text.split("(")[0] if "(" in text else text
            is_write = False
            if node.parent and node.parent.type == "assignment":
                for lc in node.parent.children:
                    if lc.type in ("global_array", "_multiple_assignment_identifiers") and lc == node:
                        is_write = True; break
            entry = {"pattern": text, "line": node.start_point[0]+1, "label": current[0]}
            if is_write: gmap[base]["writes"].append(entry)
            else: gmap[base]["reads"].append(entry)
            gmap[base]["routines"].add(current[0])
        for child in node.children: walk(child)

    walk(tree.root_node)
    return {k: {"reads":v["reads"],"writes":v["writes"],"routines":sorted(v["routines"])} for k,v in gmap.items()}

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = extract_globals(filepath)
    out_path = Path("output") / Path(filepath).stem / f"{Path(filepath).stem}_globals.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} globals → {out_path}")
