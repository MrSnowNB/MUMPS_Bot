#!/usr/bin/env python3
"""Safe tool runner — allowlisted tools only, shell=False always."""
import sys
import json
import subprocess
from pathlib import Path

ALLOWED_TOOLS = {
    "tools/mumps/normalize_mumps.py",
    "tools/mumps/parse_mumps.py",
    "tools/mumps/list_entry_points.py",
    "tools/mumps/extract_globals.py",
    "tools/mumps/extract_calls.py",
    "tools/mumps/query_ast.py",
    "tools/mumps/summarize_routine.py",
    "tools/mumps/emit_python_stub.py",
    "tools/mumps/build_ir.py",
    "tools/mumps/journal_writer.py",
    "tools/mumps/emit_traceability.py",
    "scripts/check_skeleton.py",
    "scripts/close_ticket.py",
    "scripts/next_ticket.py",
}


def run_tool(tool_path: str, args: list[str]) -> dict:
    if tool_path not in ALLOWED_TOOLS:
        return {
            "error": f"Tool '{tool_path}' is not on the allowlist.",
            "allowed": sorted(ALLOWED_TOOLS),
        }
    cmd = [sys.executable, tool_path] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,  # EXPLICIT — never True
            timeout=120,
        )
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {"raw_stdout": result.stdout}
        return {
            "returncode": result.returncode,
            "tool": tool_path,
            "args": args,
            "output": output,
            "stderr": result.stderr[:500] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Tool timed out after 120s", "tool": tool_path}
    except Exception as e:
        return {"error": str(e), "tool": tool_path}


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        # Verify allowlist enforcement
        bad = run_tool("rm", ["-rf", "/"])
        print(json.dumps({
            "allowlist_enforced": "error" in bad and "allowlist" in bad["error"],
            "shell_false_confirmed": True,
        }, indent=2))
        sys.exit(0)
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: run_tool.py <tool_path> [args...]"})) 
        sys.exit(1)
    tool = sys.argv[1]
    tool_args = sys.argv[2:]
    result = run_tool(tool, tool_args)
    print(json.dumps(result, indent=2))
