# Ticket Schema Reference

Every ticket YAML must conform to this schema. Cline reads the schema before
executing any ticket to validate structure.

```yaml
id: string                  # e.g. MUM-T01
family: string              # MUM | BUILD | ROOK | HARN
status: OPEN                # always OPEN when in tickets/open/
priority: int               # 1 (highest) – 5 (lowest)
depends_on: [string]        # list of ticket IDs that must be CLOSED first

title: string
goal: string                # one sentence, starts with a verb

context_files:              # files Cline must read before starting
  - path: string
    purpose: string

allowed_tools: [string]     # strict whitelist — no other tools permitted

task_steps:                 # ordered list; each step maps to one tool call
  - step: int
    action: string
    tool: string
    input: {}
    output_path: string

acceptance_criteria:        # ALL must pass to mark CLOSED
  - id: string              # e.g. AC-01
    test: string            # exact shell command or assertion
    expected: string

log_on_close:               # appended to luffy-journal.jsonl on CLOSED
  artifacts: [string]       # output files produced
  notes: string
```

## Validation Rules

1. `depends_on` tickets must be in `tickets/closed/` before this ticket can run.
2. `allowed_tools` is a hard whitelist — any tool call not in this list is a policy violation.
3. Every `task_steps[].tool` must appear in `allowed_tools`.
4. `acceptance_criteria` must be testable without human judgment — shell commands, JSON schema checks, or `python -m py_compile`.
5. `status` field in the YAML is informational only — the filesystem location (open/in_progress/closed/failed) is authoritative.
