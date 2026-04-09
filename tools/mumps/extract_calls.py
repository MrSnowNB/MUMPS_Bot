"""Tool: extract_calls — build cross-routine call graph from MUMPS routine."""
import json, sys
from pathlib import Path

def extract_calls(filepath: str) -> list:
    from tree_sitter import Language, Parser
    grammar_path = Path(__file__).parent / "build" / "mumps.so"
    MUMPS_LANGUAGE = Language(str(grammar_path), "mumps")
    parser = Parser(); parser.set_language(MUMPS_LANGUAGE)
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    calls = []
    current = ["ROUTINE_LEVEL"]

    def parse_ref(text):
        text = text.strip().lstrip("$")
        if "^" in text:
            parts = text.split("^")
            return parts[0].split("(")[0] if parts[0] else "", parts[1].split("(")[0] if len(parts)>1 else ""
        return text.split("(")[0], ""

    def walk(node):
        if node.type == "routine_definition":
            lbl = next((c for c in node.children if c.type == "label"), None)
            if lbl: current[0] = lbl.text.decode("utf-8", errors="replace").strip()
        if node.type == "routine_call":
            text = node.text.decode("utf-8", errors="replace").strip()
            to_label, to_routine = parse_ref(text)
            if to_routine:
                call_type = "extrinsic_function" if "$$" in text else "do"
                if node.parent and node.parent.type == "goto_command": call_type = "goto"
                calls.append({"from_label":current[0],"to_label":to_label,"to_routine":to_routine,
                    "call_type":call_type,"raw_text":text,"line":node.start_point[0]+1})
        for child in node.children: walk(child)

    walk(tree.root_node)
    return calls

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = extract_calls(filepath)
    out_path = Path("output") / Path(filepath).stem / f"{Path(filepath).stem}_calls.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: {len(result)} calls → {out_path}")
