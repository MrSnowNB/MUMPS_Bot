#!/usr/bin/env python3
"""Stage 2b: Extract entry points (labels) and line ranges from AST JSON."""
import sys
import json
from pathlib import Path


def find_labels(node: dict, labels: list) -> None:
    """Recursively find label nodes in the AST."""
    if node.get("node_type") in ("label", "routine_label", "entryref", "tag"):
        labels.append({
            "label": node.get("raw_text", "").strip(),
            "source_file": node.get("source_file", ""),
            "start_line": node.get("source_line", 0),
        })
    for child in node.get("children", []):
        find_labels(child, labels)


def assign_end_lines(labels: list, total_lines: int) -> list:
    """Assign end_line to each entry point based on next label start."""
    result = []
    for i, ep in enumerate(labels):
        end_line = labels[i + 1]["start_line"] - 1 if i + 1 < len(labels) else total_lines
        result.append({
            "label": ep["label"],
            "source_file": ep["source_file"],
            "start_line": ep["start_line"],
            "end_line": end_line,
        })
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: list_entry_points.py <input.ast.json> [output.json]"}))
        sys.exit(1)
    ast_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("output") / (ast_path.stem.replace(".ast", "") + ".entry_points.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ast_data = json.loads(ast_path.read_text())
    ast_root = ast_data.get("ast", ast_data)
    labels: list = []
    find_labels(ast_root, labels)
    labels.sort(key=lambda x: x["start_line"])
    # Estimate total lines from AST raw_text newline count
    raw = ast_root.get("raw_text", "")
    total_lines = raw.count("\n") + 1
    entry_points = assign_end_lines(labels, total_lines)
    result = {
        "entry_point_count": len(entry_points),
        "all_have_line_ranges": all(
            ep["start_line"] > 0 and ep["end_line"] >= ep["start_line"]
            for ep in entry_points
        ),
        "entry_points": entry_points,
    }
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "entry_points"}, indent=2))
