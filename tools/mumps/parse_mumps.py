"""Tool: parse_mumps — parse a MUMPS .m file with tree-sitter. Writes AST JSON.

Usage:
    python tools/mumps/parse_mumps.py <filepath.m>

Output:
    output/<ROUTINE>-ast.json  — pure JSON, keys: routine, filepath, ast

Dependency: bash scripts/build_mumps_grammar.sh
"""
import json
import sys
from pathlib import Path


def parse_mumps(filepath: str) -> dict:
    from mumps_grammar import get_mumps_language, get_mumps_parser
    language = get_mumps_language()
    parser = get_mumps_parser()
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)

    def node_to_dict(node):
        r = {
            "type": node.type,
            "start_point": list(node.start_point),
            "end_point": list(node.end_point),
        }
        if node.child_count == 0:
            r["text"] = node.text.decode("utf-8", errors="replace")
        else:
            r["children"] = [node_to_dict(c) for c in node.children]
        return r

    return {
        "routine": Path(filepath).stem,
        "filepath": str(filepath),
        "ast": node_to_dict(tree.root_node),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_mumps.py <filepath.m>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    result = parse_mumps(filepath)
    out_path = Path("output") / f"{Path(filepath).stem}-ast.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: AST written to {out_path}")
