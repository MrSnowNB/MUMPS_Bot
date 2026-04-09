"""Tool: parse_mumps — parse a MUMPS .m routine file with tree-sitter. Writes AST JSON."""
import json, sys
from pathlib import Path

def parse_mumps(filepath: str) -> dict:
    from tree_sitter import Language, Parser
    grammar_path = Path(__file__).parent / "build" / "mumps.so"
    MUMPS_LANGUAGE = Language(str(grammar_path), "mumps")
    parser = Parser(); parser.set_language(MUMPS_LANGUAGE)
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)

    def node_to_dict(node):
        r = {"type": node.type, "start_point": list(node.start_point), "end_point": list(node.end_point)}
        if node.child_count == 0: r["text"] = node.text.decode("utf-8", errors="replace")
        else: r["children"] = [node_to_dict(c) for c in node.children]
        return r

    return {"routine": Path(filepath).stem, "filepath": str(filepath), "ast": node_to_dict(tree.root_node)}

if __name__ == "__main__":
    filepath = sys.argv[1]
    result = parse_mumps(filepath)
    out_path = Path("output") / Path(filepath).stem / f"{Path(filepath).stem}_ast.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: AST written to {out_path}")
