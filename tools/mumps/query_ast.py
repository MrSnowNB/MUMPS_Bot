"""Tool: query_ast — run S-expression queries against MUMPS AST.

Usage:
    python tools/mumps/query_ast.py <filepath.m>

Output:
    output/<ROUTINE>-queries.json  — JSON dict with keys:
        lock_statements, goto_commands, postconditionals
        each a list of {line, text}

Dependency: pip install tree-sitter-languages>=1.10.2
"""
import json
import sys
from pathlib import Path

# S-expression patterns for MUMPS complexity markers.
# These are best-effort text-scan fallbacks if tree-sitter query API
# doesn't support a pattern — the AST walk is the authoritative path.
QUERY_PATTERNS = {
    "lock_statements": "lock",
    "goto_commands": "goto",
    "postconditionals": ":",
}


def query_ast(filepath: str) -> dict:
    from mumps_grammar import get_mumps_language, get_mumps_parser
    language = get_mumps_language()
    parser = get_mumps_parser()
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)

    results = {
        "lock_statements": [],
        "goto_commands": [],
        "postconditionals": [],
    }

    def walk(node):
        t = node.type.lower()
        text = node.text.decode("utf-8", errors="replace") if node.child_count == 0 else ""
        line = node.start_point[0] + 1

        if t in ("lock_command", "lock"):
            results["lock_statements"].append(
                {"line": line, "text": node.text.decode("utf-8", errors="replace").strip()}
            )
        if t in ("goto_command", "goto"):
            results["goto_commands"].append(
                {"line": line, "text": node.text.decode("utf-8", errors="replace").strip()}
            )
        if t == "postconditional":
            results["postconditionals"].append(
                {"line": line, "text": node.text.decode("utf-8", errors="replace").strip()}
            )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: query_ast.py <filepath.m>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    result = query_ast(filepath)
    out_path = Path("output") / f"{Path(filepath).stem}-queries.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"OK: queries written to {out_path}")
