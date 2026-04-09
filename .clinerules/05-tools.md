# Atomic Tool Definitions

These are the only MUMPS analysis tools available to the executor. Each tool has
a single responsibility and a deterministic output schema. Never chain tool logic
inside a single call — one tool, one purpose.

All tools require `pip install tree-sitter-languages>=1.10.2` except
`summarize_routine` and `emit_python_stub` (stdlib only).

---

## 1. `parse_mumps`

**Purpose:** Parse a `.m` MUMPS source file into a full AST using tree-sitter-mumps.

**Script:** `tools/mumps/parse_mumps.py <filepath.m>`

**Output:** `output/<ROUTINE>-ast.json`
```json
{
  "routine": "ORQQPL1",
  "filepath": "routines/ORQQPL1.m",
  "ast": { "type": "program", "children": [...] }
}
```

**Acceptance:** File exists, `ast.type == "program"`, `routine` is non-empty string.

---

## 2. `list_entry_points`

**Purpose:** Extract all label (entry point) definitions with line ranges.

**Script:** `tools/mumps/list_entry_points.py <filepath.m>`

**Output:** `output/<ROUTINE>-entry-points.json` — JSON array
```json
[
  {"label": "EN", "args": [], "line_start": 1, "line_end": 24, "line_count": 24}
]
```

**Acceptance:** Array length > 0, every object has `label`, `line_start`, `line_end`.
Extra keys (`args`, `line_count`) are permitted.

---

## 3. `extract_globals`

**Purpose:** Map every global variable read/write, indexed by global name.

**Script:** `tools/mumps/extract_globals.py <filepath.m>`

**Output:** `output/<ROUTINE>-globals.json` — JSON dict keyed by global name
```json
{
  "^DPT": {
    "reads":  [{"pattern": "^DPT(DFN,0)", "line": 5, "label": "EN"}],
    "writes": [{"pattern": "^DPT(DFN,.01)", "line": 10, "label": "SETDPT"}]
  }
}
```

**Acceptance:** Keys are global names. Each value has `reads` and `writes` arrays.
Each entry has `pattern`, `line`, `label`.

---

## 4. `extract_calls`

**Purpose:** Build the cross-routine call graph. Identifies DO, GOTO, and extrinsic calls.

**Script:** `tools/mumps/extract_calls.py <filepath.m>`

**Output:** `output/<ROUTINE>-calls.json` — flat JSON array
```json
[
  {"caller": "EN", "callee": "SETDPT^ROUTINE", "call_type": "do", "line": 12}
]
```

**Acceptance:** Array of objects, each with `caller`, `callee`, `call_type`, `line`.
`call_type` is one of: `do`, `goto`, `extrinsic_function`.

---

## 5. `query_ast`

**Purpose:** Run preset AST queries for complexity markers (LOCK, GOTO, postconditions).

**Script:** `tools/mumps/query_ast.py <filepath.m>`

**Output:** `output/<ROUTINE>-queries.json`
```json
{
  "lock_statements":  [{"line": 45, "text": "LOCK +^DPT(DFN)"}],
  "goto_commands":    [{"line": 89, "text": "GOTO END"}],
  "postconditionals": [{"line": 12, "text": ":DFN"}]
}
```

**Acceptance:** Dict with keys `lock_statements`, `goto_commands`, `postconditionals`.
Each is a list of `{line, text}` objects (may be empty).

---

## 6. `summarize_routine`

**Purpose:** Synthesize per-entry-point metadata from prerequisite JSONs.

**Script:** `tools/mumps/summarize_routine.py <filepath.m> --entries <path> --globals <path> --calls <path>`

**Output:** `output/<ROUTINE>-summary.json`
```json
{
  "routine_name": "ORQQPL1",
  "entry_point_count": 12,
  "global_count": 5,
  "call_count": 8,
  "complexity_flags": ["LOCK/UNLOCK", "FileMan DIE call"],
  "entry_points": [...]
}
```

**Acceptance:** Dict with keys `routine_name`, `entry_point_count`, `global_count`,
`call_count`, `complexity_flags`. All counts are integers, `complexity_flags` is a list.

---

## 7. `emit_python_stub`

**Purpose:** Generate typed Python stubs with docstrings and TODO markers.

**Script:** `tools/mumps/emit_python_stub.py <summary.json>`

**Output:** `output/<ROUTINE>-stub.py`

**Acceptance:** File contains `def ` and type annotations. One function per entry point.
