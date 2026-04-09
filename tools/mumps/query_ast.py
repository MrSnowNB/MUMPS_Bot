"""
Tool: query_ast — run S-expression query against MUMPS AST
"""
import json, sys
from pathlib import Path

def query_ast(filepath: str, s_expression: str) -> list:
    from tree_sitter import Language, Parser
    grammar_path = Path(__file__).parent / "build" / "mumps.so"
    MUMPS_LANGUAGE = Language(str(grammar_path), "mumps")
    parser = Parser(); parser.set_language(MUMPS_LANGUAGE)
    source = Path(filepath).read_bytes()
    tree = parser.parse(source)
    query = MUMPS_LANGUAGE.query(s_expression)
    captures = query.captures(tree.root_node)
    results = []
    for name, nodes in captures.items():
        node_list = nodes if isinstance(nodes, list) else [nodes]
        for node in node_list:
            results.append({"capture_name": name, "node_type": node.type,
                "text": node.text.decode("utf-8", errors="replace"),
                "start_line": node.start_point[0]+1, "end_line": node.end_point[0]+1})
    return results

if __name__ == "__main__":
    result = query_ast(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
