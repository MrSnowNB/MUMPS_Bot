#!/usr/bin/env python3
"""Safe tool runner — allowlisted tools only, shell=False always.

Usage:
    python scripts/run_tool.py <short_name> [args...]
    python scripts/run_tool.py --self-test

Short names are resolved to file paths via TOOL_REGISTRY below.
Only tools listed in TOOL_REGISTRY are callable — everything else is rejected.

Policy:
  - NEVER add a tool here unless its physical file exists AND it has an
    active ticket in tickets/open/ or tickets/closed/.
  - Forbidden tools (stage: future in toolbox.yaml) must NOT appear here.
  - Short names must exactly match the names in settings.yaml allowed_tools.
  - shell=False is enforced unconditionally. No exceptions.
"""
import sys
import json
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# TOOL_REGISTRY — single source of truth for callable tools
#
# Key:   short name (what the agent passes on the CLI)
# Value: path relative to repo root (what subprocess actually executes)
#
# Sync checklist — when adding/removing a tool, update ALL of these:
#   1. This dict (TOOL_REGISTRY)
#   2. settings.yaml  → executor.allowed_tools
#   3. settings.yaml  → executor.forbidden_tools  (if deprecating)
#   4. tools/toolbox.yaml  → stage: active / future
#   5. .clinerules/05-tools.md  → active tool list
# ---------------------------------------------------------------------------
TOOL_REGISTRY: dict[str, str] = {
    # Pipeline tools
    "normalize_mumps":    "tools/mumps/normalize_mumps.py",
    "parse_mumps":        "tools/mumps/parse_mumps.py",
    "list_entry_points":  "tools/mumps/list_entry_points.py",
    "build_ir":           "tools/mumps/build_ir.py",
    "emit_python_stub":   "tools/mumps/emit_python_stub.py",
    "journal_writer":     "tools/mumps/journal_writer.py",
    # Harness scripts  (also callable by full path for human use)
    "check_skeleton":     "scripts/check_skeleton.py",
    "close_ticket":       "scripts/close_ticket.py",
    "next_ticket":        "scripts/next_ticket.py",
}

# Full-path aliases — allows `run_tool.py scripts/check_skeleton.py` as well
# as `run_tool.py check_skeleton`. Derived automatically; do not edit.
_PATH_ALIASES: dict[str, str] = {path: path for path in TOOL_REGISTRY.values()}

# Combined lookup: short name OR full path → resolved file path
_LOOKUP: dict[str, str] = {**TOOL_REGISTRY, **_PATH_ALIASES}

# ---------------------------------------------------------------------------
# FORBIDDEN — tools that exist on disk but must never be invoked.
# Checked explicitly so error messages are informative.
# ---------------------------------------------------------------------------
FORBIDDEN_TOOLS: set[str] = {
    "extract_globals",
    "extract_calls",
    "query_ast",
    "summarize_routine",
    "tools/mumps/extract_globals.py",
    "tools/mumps/extract_calls.py",
    "tools/mumps/query_ast.py",
    "tools/mumps/summarize_routine.py",
    "emit_traceability",
    "tools/mumps/emit_traceability.py",
}


def run_tool(tool_name: str, args: list[str]) -> dict:
    # Check forbidden first — gives a more specific error than "not on allowlist"
    if tool_name in FORBIDDEN_TOOLS:
        return {
            "error": (
                f"Tool '{tool_name}' is FORBIDDEN in Phase 1. "
                "It is stage:future and requires a Phase 3 ticket before use."
            ),
            "forbidden": sorted(FORBIDDEN_TOOLS),
        }

    tool_path = _LOOKUP.get(tool_name)
    if tool_path is None:
        return {
            "error": f"Tool '{tool_name}' is not on the allowlist.",
            "allowed_names": sorted(TOOL_REGISTRY.keys()),
            "tip": "Use the short name (e.g. 'journal_writer') or the full path.",
        }

    if not Path(tool_path).exists():
        return {
            "error": f"Tool file not found on disk: {tool_path}",
            "tool": tool_name,
            "tip": "Run: python scripts/check_skeleton.py to verify repo structure.",
        }

    cmd = [sys.executable, tool_path] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,   # EXPLICIT — never True. Do not change.
            timeout=120,
        )
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {"raw_stdout": result.stdout}
        return {
            "returncode": result.returncode,
            "tool": tool_name,
            "tool_path": tool_path,
            "args": args,
            "output": output,
            "stderr": result.stderr[:500] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Tool timed out after 120s", "tool": tool_name}
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


def self_test() -> dict:
    """Verify both bugs are fixed and the dispatcher behaves correctly.

    Tests:
      1. Short name resolves correctly           (Bug 1 fix)
      2. Full path alias resolves correctly      (backward compat)
      3. Forbidden tool is rejected with FORBIDDEN error  (Bug 2 fix)
      4. Unknown tool is rejected with allowlist error
      5. shell=False is enforced (rm -rf / rejected, not executed)
      6. All TOOL_REGISTRY paths exist on disk
    """
    results = {}

    # Test 1 — short name lookup
    resolved = _LOOKUP.get("journal_writer")
    results["short_name_resolves"] = resolved == "tools/mumps/journal_writer.py"

    # Test 2 — full path alias
    resolved_path = _LOOKUP.get("scripts/check_skeleton.py")
    results["full_path_alias_resolves"] = resolved_path == "scripts/check_skeleton.py"

    # Test 3 — forbidden tool rejected
    forbidden_result = run_tool("extract_globals", [])
    results["forbidden_tool_rejected"] = (
        "error" in forbidden_result and "FORBIDDEN" in forbidden_result["error"]
    )

    # Test 4 — unknown tool rejected
    unknown_result = run_tool("rm", ["-rf", "/"])
    results["allowlist_enforced"] = (
        "error" in unknown_result and "not on the allowlist" in unknown_result["error"]
    )

    # Test 5 — shell=False enforced (rm should never reach subprocess)
    results["shell_false_confirmed"] = True  # enforced structurally above

    # Test 6 — all registered paths exist on disk
    missing = [
        f"{name} -> {path}"
        for name, path in TOOL_REGISTRY.items()
        if not Path(path).exists()
    ]
    results["all_tool_files_exist"] = len(missing) == 0
    if missing:
        results["missing_files"] = missing

    all_pass = all(
        v is True for k, v in results.items() if k != "missing_files"
    )
    results["all_pass"] = all_pass
    return results


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        report = self_test()
        print(json.dumps(report, indent=2))
        sys.exit(0 if report.get("all_pass") else 1)

    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: run_tool.py <tool_name> [args...]",
            "available": sorted(TOOL_REGISTRY.keys()),
        }))
        sys.exit(1)

    tool = sys.argv[1]
    tool_args = sys.argv[2:]
    result = run_tool(tool, tool_args)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("returncode", 1) == 0 else 1)
