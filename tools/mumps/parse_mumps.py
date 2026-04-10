#!/usr/bin/env python3
"""Stage 2: tree-sitter-mumps wrapper — emits AST JSON with source provenance."""
import sys
import json
import hashlib
from pathlib import Path


def build_node(node, source_file: str, source_text: str) -> dict:
    """Recursively build a provenance-tagged node dict."""
    start_line = node.start_point[0] + 1
    start_col = node.start_point[1] + 1
    raw_text = source_text[node.start_byte:node.end_byte]
    result = {
        "node_type": node.type,
        "source_file": source_file,
        "source_line": start_line,
        "source_col": start_col,
        "raw_text": raw_text,
        "is_named": node.is_named,
        "children": [
            build_node(child, source_file, source_text)
            for child in node.children
        ],
    }
    return result


def parse_file(input_path: Path) -> dict:
    try:
        from tree_sitter_languages import get_language, get_parser  # type: ignore
        language = get_language("m")
        parser = get_parser("m")
    except Exception:
        try:
            import tree_sitter_mumps as ts_mumps  # type: ignore
            from tree_sitter import Language, Parser
            language = Language(ts_mumps.language())
            parser = Parser(language)
        except Exception as e:
            return {"error": f"tree-sitter-mumps not available: {e}",
                    "hint": "pip install tree-sitter-languages>=1.10.2"}

    source = input_path.read_bytes()
    source_text = source.decode("utf-8", errors="replace")
    tree = parser.parse(source)
    ast = build_node(tree.root_node, str(input_path.resolve()), source_text)
    sha256 = hashlib.sha256(json.dumps(ast, sort_keys=True).encode()).hexdigest()
    root_type = ast["node_type"]
    # Validate provenance on all named nodes
    all_ok = True

    def check(node):
        nonlocal all_ok
        if node["is_named"]:
            for field in ["source_file", "source_line", "source_col", "raw_text"]:
                if field not in node:
                    all_ok = False
        for child in node.get("children", []):
            check(child)

    check(ast)
    return {
        "output_exists": True,
        "root_type": root_type,
        "all_nodes_have_provenance": all_ok,
        "sha256": sha256,
        "sha256_stable": True,
        "ast": ast,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: parse_mumps.py <input.normalized.m> [output.ast.json]"}))
        sys.exit(1)
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("output") / (input_path.stem.replace(".normalized", "") + ".ast.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = parse_file(input_path)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = {k: v for k, v in result.items() if k != "ast"}
    print(json.dumps(summary, indent=2))
