# Atomic Tool Definitions — Phase 1 Minimal Toolset

These are the ONLY tools available to the executor in Phase 1.
The toolset is intentionally minimal — every tool added increases
the failure surface. New tools are added iteratively as tickets demand them.

All parse-related tools depend on the MUMPS grammar shim:
  - File: `tools/mumps/mumps_grammar.py`
  - Classification: zero-order primitive (internal library, not callable)
  - Build the grammar first: `bash scripts/build_mumps_grammar.sh`
  - The shim auto-detects tree-sitter-languages (Python ≤3.12) or locally
    compiled vendor/mumps.so or vendor/mumps.dylib (Python 3.13+)

## FORBIDDEN tools (physically exist but stage: future)

The following tools exist in tools/mumps/ but are NOT callable.
Do not invoke them. Do not add them to any ticket's steps.
They are blocked until Phase 3 tickets are created and approved:

  - extract_globals    (Phase 3 — whole-codebase schema pass required)
  - extract_calls      (Phase 3 — meaningful only after multi-routine analysis)
  - query_ast          (Phase 3 — Rook lint-chain integration)
  - summarize_routine  (Phase 3 — blocked by extract_globals + extract_calls)

---

## Harness Scripts

### `check_skeleton`
**Purpose:** Verify all required skeleton directories exist and are writable.
**Script:** `scripts/check_skeleton.py`
**Ticket:** BOOT-T01
**Output:** Pass/fail report to stdout. Creates missing dirs with .gitkeep.
**Acceptance:** Exit code 0, all required dirs confirmed.

### `next_ticket`
**Purpose:** Return the next open ticket with all dependencies satisfied.
**Script:** `scripts/next_ticket.py`
**Output:** Ticket ID + title to stdout. `--all` flag shows full ready queue.
**Acceptance:** Returns a valid ticket ID or "No ready tickets."

### `close_ticket`
**Purpose:** Gate-enforced ticket closer. Verifies REASONING + VERIFY + artifact.
**Script:** `scripts/close_ticket.py --ticket <ID> [--dry-run]`
**Output:** Moves ticket YAML to tickets/closed/. Moves to failed/ on gate fail.
**Acceptance:** Ticket file appears in tickets/closed/.

### `run_tool`
**Purpose:** Safe allowlisted tool dispatcher. Never call pipeline tools directly.
**Script:** `scripts/run_tool.py <tool_name> [args...]`
**Output:** Delegates to the named tool. Rejects non-allowlisted names.
**Acceptance:** Exit code 0 = tool ran. Exit code 1 = rejected or error.

---

## Pipeline Tools — Execution Order

### Stage 1 — `normalize_mumps`
**Purpose:** Expand MUMPS abbreviations to full canonical form.
**Script:** `tools/mumps/normalize_mumps.py <filepath.m>`
**Ticket:** PIPE-T01
**Output:** `output/<ROUTINE>/<ROUTINE>.normalized.m`
```
S -> SET     W -> WRITE     Q -> QUIT
$P -> $PIECE  $G -> $GET     $L -> $LENGTH
```
**Acceptance:** Output file exists, zero abbreviations remain in known COMMAND_MAP.

---

### Stage 2 — `parse_mumps`
**Purpose:** Parse normalized .m file into AST JSON using tree-sitter-mumps.
**Script:** `tools/mumps/parse_mumps.py <filepath.normalized.m>`
**Ticket:** PIPE-T02
**Output:** `output/<ROUTINE>/<ROUTINE>.ast.json`
```json
{
  "routine": "ORQQPL1",
  "source_file": "routines/ORQQPL1.m",
  "ast": { "type": "program", "children": [...] }
}
```
**Acceptance:** File exists, `ast.type == "program"`, `routine` is non-empty.
Error nodes (`type == "ERROR"`) must be logged to journal but do not fail this stage.

---

### Stage 2b — `list_entry_points`
**Purpose:** Extract all labeled entry points with line ranges from AST JSON.
**Script:** `tools/mumps/list_entry_points.py <ast.json>`
**Ticket:** PIPE-T03
**Output:** `output/<ROUTINE>/<ROUTINE>.entry_points.json`
```json
[
  {"label": "EN", "args": [], "line_start": 1, "line_end": 24, "line_count": 24}
]
```
**Acceptance:** Array length > 0, every object has `label`, `line_start`, `line_end`.

---

### Stage 4 — `build_ir`
**Purpose:** Build minimal Pydantic v2 IR from AST JSON + entry points JSON.
**Script:** `tools/mumps/build_ir.py <ast.json> <entry_points.json>`
**Ticket:** PIPE-T04
**Output:** `output/<ROUTINE>/<ROUTINE>.ir.json`
**Requires:** `pydantic>=2.0` (see requirements.txt)
**Acceptance:** Valid JSON, every node has `node_id` (UUID), `source_line`, `raw_mumps`.

---

### Stage 5 — `emit_python_stub`
**Purpose:** Rule-based Python stub emitter from IR JSON.
**Script:** `tools/mumps/emit_python_stub.py <ir.json>`
**Ticket:** PIPE-T05
**Output:** `output/<ROUTINE>/stubs.py` + `output/<ROUTINE>/stubs.traceability.jsonl`
**Rule:** Unresolvable constructs → `# TODO: HRQ-PENDING` comment. Never guessed code.
**Acceptance:** File contains `def `, type annotations, one function per entry point.
  Traceability JSONL exists and has one row per IR node.

---

### `journal_writer`
**Purpose:** Append-only dual journal writer for all REASONING and VERIFY events.
**Script:** `tools/mumps/journal_writer.py --ticket <ID> --event <TYPE> --payload '<JSON>'`
**Ticket:** BOOT-T02
**Output:** Appends to `logs/luffy-journal.jsonl` and `logs/scratch-<ticket_id>.jsonl`.
**Rule:** Every REASONING decision and VERIFY result MUST be logged before close_ticket runs.
**Acceptance:** Both log files exist and new entry is present.
