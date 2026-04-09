---
name: ticket-executor
description: >
  Execute a single atomic ticket from tickets/open/. Read the ticket, verify
  dependencies are closed, run all task_steps using allowed_tools, evaluate
  the gate_command, and move the ticket to closed or failed. Log everything.
version: "2.0"
last_updated: "2026-04-09"
---

# ticket-executor

## Purpose

Execute one ticket completely and deterministically. The executor has no discretion
about which ticket to pick — that is the scheduler's job. Given a ticket ID, the
executor's only job is to work through it according to the contract below.

---

## Pre-Flight Checklist

Before executing any ticket step, verify:

```
□ Ticket file exists at tickets/open/<id>.yaml
□ Ticket status is "open"
□ All depends_on IDs exist in tickets/closed/
□ All context_files listed in ticket exist on disk
□ result_path parent directory exists (create if not)
□ allowed_tools are available at current agent.stage
```

If any check fails: write ISSUE.md, halt. Do not begin execution.

---

## Ticket Schema

```yaml
---
id: MUM-T01
title: "<one sentence describing the output>"
status: open          # open | in_progress | closed | failed | blocked
attempts: 0
max_retries: 2
depends_on: []        # list of ticket IDs that must be CLOSED first
context_files:
  - path/to/file.m   # files the executor must read before starting
allowed_tools:
  - read_file
  - write_file
  - exec_python
task_steps:
  - "Step description (imperative, no markdown)"
gate_command: "pytest -q tests/test_MUM_T01.py"
acceptance_criteria: "All assertions pass; result_path file exists and is valid YAML"
result_path: output/MUM-T01-result.yaml
---
```

The executor reads this file and executes it literally. It does NOT interpret intent
beyond what is written. If a step is ambiguous, write ISSUE.md and halt.

---

## Execution Loop

```
1.  read_file(tickets/open/<id>.yaml)          → load ticket
2.  verify pre-flight checklist                → halt on any failure
3.  write_file(tickets/in_progress/<id>.yaml)  → status: in_progress
4.  for step in task_steps:
      a. apply first-principles chain (00-policy.md)
      b. call one allowed_tool
      c. wait for result
      d. append to logs/session_<date>.jsonl
      e. if result is ERROR: check retry budget → halt or retry
5.  exec_python(gate_command)                  → capture stdout/stderr
6.  if gate GREEN:
      write result to result_path
      move ticket to tickets/closed/<id>.yaml  → status: closed
      append CLOSED entry to logs/journal.md
7.  if gate RED:
      increment attempts
      if attempts >= max_retries:
        move to tickets/failed/<id>.yaml       → status: failed
        trigger 03-failure-handling.md
      else:
        move back to tickets/open/<id>.yaml    → status: open
```

---

## Logging Contract

Every tool call must produce one JSONL entry appended to `logs/session_<date>.jsonl`:

```json
{
  "ts": "2026-04-09T10:35:00Z",
  "ticket_id": "MUM-T01",
  "step": 1,
  "tool": "read_file",
  "path": "path/to/file.m",
  "result": "ok | error: <message>",
  "tokens_used": 0
}
```

`tokens_used` is 0 when not available from the execution environment. The field
must always be present for schema consistency.

---

## Output Validation

Before writing the result to `result_path`, verify:

1. **Format** — is the output valid YAML or Markdown with frontmatter?
2. **Completeness** — does it contain all fields listed in `acceptance_criteria`?
3. **Gate** — did `gate_command` exit 0?

If any check fails: do not write the result. Increment attempts. Handle per step 7 above.

---

## Prohibited Actions During Execution

- Do not read tickets from `tickets/failed/` unless the ticket spec says so
- Do not write to `tickets/closed/` except as the final step of a successful execution
- Do not call tools not listed in the ticket's `allowed_tools`
- Do not modify `depends_on` or any ticket's DAG structure
- Do not spawn parallel executions
