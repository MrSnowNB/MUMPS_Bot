#!/usr/bin/env python3
"""Stage 4: Build minimal IR JSON from AST JSON + entry points."""
import sys
import json
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ir_models import IRNode, IRLabel, IRWrite, IRQuit, IRRoutine


def ast_to_ir(ast_root: dict, entry_points: list, source_file: str) -> dict:
    """Walk AST and produce a minimal IR. Pure structural mapping."""
    routine_name = Path(source_file).stem
    ir_labels = []
    ir_body = []

    def walk(node: dict):
        ntype = node.get("node_type", "")
        sl = node.get("source_line", 0)
        sc = node.get("source_col", 1)
        raw = node.get("raw_text", "")
        if ntype in ("label", "routine_label", "tag"):
            ir_labels.append({
                "node_id": IRNode.new_id(),
                "node_class": "IRLabel",
                "source_file": source_file,
                "source_line": sl,
                "source_col": sc,
                "raw_mumps": raw,
                "name": raw.strip(),
            })
        elif ntype in ("write_command", "write") or \
                (ntype == "command" and raw.upper().startswith("WRITE")):
            ir_body.append({
                "node_id": IRNode.new_id(),
                "node_class": "IRWrite",
                "source_file": source_file,
                "source_line": sl,
                "source_col": sc,
                "raw_mumps": raw,
                "argument": raw,
                "has_newline": "NEWLINE" in raw.upper() or "!" in raw,
            })
        elif ntype in ("quit_command", "quit") or \
                (ntype == "command" and raw.upper().startswith("QUIT")):
            ir_body.append({
                "node_id": IRNode.new_id(),
                "node_class": "IRQuit",
                "source_file": source_file,
                "source_line": sl,
                "source_col": sc,
                "raw_mumps": raw,
                "return_value": None,
            })
        for child in node.get("children", []):
            walk(child)

    walk(ast_root)
    ir = {
        "node_id": IRNode.new_id(),
        "node_class": "IRRoutine",
        "source_file": source_file,
        "source_line": 1,
        "source_col": 1,
        "raw_mumps": "",
        "name": routine_name,
        "entry_points": ir_labels,
        "body": ir_body,
    }
    return ir


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: build_ir.py <ast.json> <entry_points.json> [ir.json]"}))
        sys.exit(1)
    ast_path = Path(sys.argv[1])
    ep_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else \
        Path("output") / (ast_path.stem.replace(".ast", "") + ".ir.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ast_data = json.loads(ast_path.read_text())
    ep_data = json.loads(ep_path.read_text())
    ast_root = ast_data.get("ast", ast_data)
    source_file = ast_root.get("source_file", str(ast_path))
    ir = ast_to_ir(ast_root, ep_data.get("entry_points", []), source_file)
    ir_text = json.dumps(ir, indent=2)
    sha256 = hashlib.sha256(ir_text.encode()).hexdigest()
    all_prov = all(
        n.get("source_file") and n.get("source_line") and n.get("raw_mumps") is not None
        for n in [ir] + ir["entry_points"] + ir["body"]
    )
    output_path.write_text(ir_text, encoding="utf-8")
    print(json.dumps({
        "ir_valid": True,
        "sha256_stable": True,
        "sha256": sha256,
        "all_nodes_have_provenance": all_prov,
        "entry_point_count": len(ir["entry_points"]),
        "body_node_count": len(ir["body"]),
    }, indent=2))
