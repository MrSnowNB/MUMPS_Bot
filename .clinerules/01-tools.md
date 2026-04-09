# Atomic Tool Definitions

These are the only tools available to the executor. Each tool has a single
responsibility and a deterministic output schema. Never chain tool logic
inside a single call — one tool, one purpose.

---

## 1. `parse_mumps`

**Purpose:** Parse a `.m` MUMPS source file into a full AST using tree-sitter-mumps.

**Input:**
```yaml
routine_path: str   # relative path to the .m file
```

**Output:** `output/{ROUTINE}-ast.json`
```json
{
  "routine": "MPIF001",
  "source_lines": 319,
  "tree": { /* tree-sitter node tree */ }
}
```

**Acceptance:** File exists, `tree.type == "program"`, `source_lines > 0`.

---

## 2. `list_entry_points`

**Purpose:** Extract all label (entry point) definitions with line ranges.

**Input:**
```yaml
ast_path: str   # path to output/{ROUTINE}-ast.json
```

**Output:** `output/{ROUTINE}-entries.json`
```json
[
  {"label": "EN", "line_start": 1, "line_end": 24},
  {"label": "SETDPT", "line_start": 25, "line_end": 51}
]
```

**Acceptance:** Array length > 0, every object has `label`, `line_start`, `line_end`.

---

## 3. `extract_globals`

**Purpose:** Map every global variable read/write to its containing entry point.

**Input:**
```yaml
ast_path: str
entries_path: str
```

**Output:** `output/{ROUTINE}-globals.json`
```json
{
  "EN": {
    "reads":  ["^DPT", "^DIC"],
    "writes": ["^DPT", "^TMP"]
  }
}
```

**Acceptance:** Keys match labels in entries_path. Each value has `reads` and `writes` arrays.

---

## 4. `extract_calls`

**Purpose:** Build the cross-routine call graph. Identifies DO, GOTO, and extrinsic calls.

**Input:**
```yaml
ast_path: str
entries_path: str
```

**Output:** `output/{ROUTINE}-calls.json`
```json
{
  "EN": [
    {"target": "SETDPT", "type": "DO", "line": 12},
    {"target": "DIE^FILEMAN", "type": "DO", "line": 18}
  ]
}
```

**Acceptance:** Keys match labels. Each call has `target`, `type` (DO/GOTO/EXTRINSIC), `line`.

---

## 5. `query_ast`

**Purpose:** Run an ad-hoc tree-sitter S-expression query against the AST.
Use for targeted searches: LOCK nodes, postconditionals, specific global patterns.

**Input:**
```yaml
ast_path: str
query: str       # tree-sitter S-expression query string
label: str       # short name for output file suffix
```

**Output:** `output/{ROUTINE}-query-{label}.json`
```json
[
  {"node_type": "lock_command", "line": 42, "text": "LOCK +^DPT(DFN)"}
]
```

**Acceptance:** File exists. Array may be empty (no matches is valid).

---

## 6. `summarize_routine`

**Purpose:** Synthesize a structured per-entry-point metadata summary from
all prior tool outputs for a routine.

**Input:**
```yaml
entries_path: str
globals_path: str
calls_path: str
routine: str
```

**Output:** `output/{ROUTINE}-summary.json`
```json
{
  "routine": "MPIF001",
  "entry_points": 17,
  "globals_accessed": ["^DPT", "^DIC", "^TMP"],
  "external_calls": ["DIE^FILEMAN", "GETS^DIQ"],
  "has_locks": true,
  "has_postconditionals": true,
  "translation_complexity": "HIGH"
}
```

**Acceptance:** All keys present. `translation_complexity` in [LOW, MEDIUM, HIGH].

---

## 7. `emit_python_stub`

**Purpose:** Generate typed Python stub functions with docstrings and TODO markers
for each entry point. One function per entry point.

**Input:**
```yaml
summary_path: str
entries_path: str
globals_path: str
calls_path: str
routine: str
```

**Output:** `output/{ROUTINE}.py`

```python
def EN(dfn: int, ien: int) -> dict:
    """
    MPIF001^EN — Patient identity merge entry point.
    Globals read:  ^DPT, ^DIC
    Globals write: ^DPT, ^TMP
    External calls: DIE^FILEMAN, GETS^DIQ
    Locks: ^DPT(DFN)
    """
    # TODO: implement
    raise NotImplementedError("MPIF001^EN not yet translated")
```

**Acceptance:** File parses as valid Python (`python -m py_compile`). One function per entry point.
