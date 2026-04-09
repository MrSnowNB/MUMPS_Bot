# Ticket Schema Reference

Every ticket YAML in `tickets/open/` must conform to this schema.
The executor validates each ticket against this schema before execution.

```yaml
---
id: string                    # e.g. "MUM-T01"
title: string                 # one sentence describing the output
status: string                # open | in_progress | closed | failed | blocked
attempts: integer             # default 0; incremented on each retry
max_retries: integer          # default 2; ticket → BLOCKED when attempts >= max_retries
depends_on: [string]          # list of ticket IDs that must be CLOSED first (or empty list)
context_files: [string]       # list of file path strings the executor must read before starting
allowed_tools: [string]       # strict whitelist of tool names — no other tools permitted
task_steps: [string]          # ordered list of instruction strings (imperative, no markdown)
gate_command: string          # pytest or shell command to run as acceptance gate
acceptance_criteria: string   # human-readable description of what constitutes a pass
result_path: string           # expected output file path (e.g. output/MUM-T01-ast.json)
---
```

## Required Fields

All fields listed above are **required**. A ticket missing any field will fail
schema validation and will not be executed.

## Validation Rules

1. `id` must be unique across all ticket directories.
2. `depends_on` tickets must be in `tickets/closed/` before this ticket can run.
3. `allowed_tools` is a hard whitelist — any tool call not in this list is a policy violation.
4. `task_steps` are executed in order. Do not skip or reorder.
5. `gate_command` must be a valid shell command that exits 0 on success.
6. `status` field in the YAML is informational — the filesystem location (open/in_progress/closed/failed) is authoritative.
7. `attempts` must be an integer >= 0.
8. `max_retries` must be an integer >= 1.
