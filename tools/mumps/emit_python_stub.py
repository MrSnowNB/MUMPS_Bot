#!/usr/bin/env python3
"""Stage 5: Emit Python stub from IR JSON with source-line trace comments."""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

RULE_VERSION = "0.1.0"

RULE_MAP = {
    "IRWrite": "RULE-WRITE-001",
    "IRQuit": "RULE-QUIT-001",
    "IRLabel": "RULE-LABEL-001",
}


def emit_stub(ir: dict, routine_name: str) -> tuple[list[str], list[dict]]:
    lines = []
    trace = []
    gen_line = 0

    def add(code: str, src_line: int, rule_id: str, ir_node_id: str, src_file: str):
        nonlocal gen_line
        gen_line += 1
        lines.append(f"{code}  # MUMPS line {src_line}")
        trace.append({
            "generated_file": f"output/{routine_name}.py",
            "generated_line": gen_line,
            "source_file": src_file,
            "source_line": src_line,
            "rule_id": rule_id,
            "rule_version": RULE_VERSION,
            "ir_node_id": ir_node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    lines.append(f"# AUTO-GENERATED STUB — {routine_name}")
    lines.append(f"# DO NOT EDIT — regenerate via emit_python_stub.py")
    lines.append(f"# Source: {ir.get('source_file', 'unknown')}")
    lines.append("")
    gen_line += 4

    for ep in ir.get("entry_points", []):
        fn_name = ep["name"].lower().replace(" ", "_") or "entry"
        add(f"def {fn_name}():", ep["source_line"],
            RULE_MAP["IRLabel"], ep["node_id"], ep["source_file"])

    lines.append("")
    gen_line += 1

    for node in ir.get("body", []):
        nc = node.get("node_class", "")
        sl = node.get("source_line", 0)
        nid = node.get("node_id", "")
        sf = node.get("source_file", "")
        if nc == "IRWrite":
            arg = node.get("argument", "")
            newline = node.get("has_newline", False)
            end = "\\n" if newline else ""
            add(f'    print({json.dumps(arg + end)})',
                sl, RULE_MAP["IRWrite"], nid, sf)
        elif nc == "IRQuit":
            ret = node.get("return_value")
            stmt = f"    return {ret}" if ret else "    return"
            add(stmt, sl, RULE_MAP["IRQuit"], nid, sf)
        else:
            add(f"    # TODO: HRQ-PENDING — unhandled node_class={nc}",
                sl, "RULE-HRQ-000", nid, sf)

    stub_text = "\n".join(lines) + "\n"
    covered = sum(1 for t in trace if "HRQ" not in t["rule_id"])
    coverage = covered / max(len(trace), 1)
    return stub_text, trace, coverage


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: emit_python_stub.py <ir.json> [output.py]"}))
        sys.exit(1)
    ir_path = Path(sys.argv[1])
    ir = json.loads(ir_path.read_text())
    routine_name = ir.get("name", ir_path.stem.replace(".ir", ""))
    output_py = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("output") / f"{routine_name}.py"
    trace_path = output_py.with_suffix(".traceability.jsonl")
    output_py.parent.mkdir(parents=True, exist_ok=True)
    stub_text, trace, coverage = emit_stub(ir, routine_name)
    output_py.write_text(stub_text, encoding="utf-8")
    trace_path.write_text(
        "\n".join(json.dumps(r) for r in trace), encoding="utf-8"
    )
    print(json.dumps({
        "stub_exists": True,
        "trace_coverage": round(coverage, 4),
        "no_llm_content": True,
        "generated_lines": len(stub_text.splitlines()),
        "trace_records": len(trace),
    }, indent=2))
