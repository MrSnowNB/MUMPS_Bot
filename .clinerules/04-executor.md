---
title: Executor Contract
version: "1.0"
scope: workspace
applies_to: executor
last_updated: "2026-04-09"
---

# Executor Contract

This rule file defines how the Cline executor processes tickets.
It is executor-agnostic: no model names, no hardware references, no endpoint URLs.
All runtime configuration lives in `settings.yaml`.

---

## Role

The executor reads one ticket at a time from `tickets/open/`, executes the task steps
using only the `allowed_tools` declared in `settings.yaml`, and moves the ticket to
`tickets/closed/` (success) or `tickets/failed/` (failure after max retries).

The executor is NOT a planner. It does not:
- Decompose goals into new tickets
- Decide which ticket to work on next (the scheduler does that)
- Modify any ticket's `depends_on` graph
- Communicate with external services not listed in `allowed_tools`

---

## Thinking Budget

- **Plan phase:** chain-of-thought reasoning allowed for ticket decomposition
- **Build phase:** suppress extended reasoning; proceed directly to tool calls
- **All other phases:** no extended reasoning

If a ticket requires more than 3 reasoning steps before the first tool call,
the ticket is not atomic — write ISSUE.md and halt.

---

## Tool Call Discipline

- One tool call per turn; wait for result before next call
- Max retries per ticket: value from `settings.yaml → executor.max_retries`
- On final retry failure: write ISSUE.md, set ticket `FAILED`, halt

---

## Forbidden Actions

- Do NOT `pip install` anything
- Do NOT register or start MCP servers
- Do NOT modify Cline config or editor settings
- Do NOT write to `tickets/closed/` directly — use the move procedure
- Do NOT read tickets in `tickets/failed/` unless explicitly instructed
- Do NOT reference or load any specific model by name in code or config

---

## Ticket Execution Procedure

1. Read ticket YAML from `tickets/open/<id>.yaml`
2. Verify all `depends_on` ticket IDs exist in `tickets/closed/`
3. Set ticket `status: in_progress`, write back to `tickets/in_progress/<id>.yaml`
4. Execute each step in `task_steps` in order using `allowed_tools`
5. Run the `gate_command`; capture stdout/stderr
6. If gate green: move ticket to `tickets/closed/`, set `status: closed`, write `result_path`
7. If gate red: increment `attempts`, check against `max_retries`
   - Under limit: reset to `tickets/open/`, set `status: open`
   - At limit: move to `tickets/failed/`, trigger failure procedure (`03-failure-handling.md`)

---

## Context Management

- At 60% context window used: write `CHECKPOINT.md` summarising completed steps, continue
- At 80% context window used: halt, write ISSUE.md, alert human

---

## Response Format

- All file outputs: Markdown with YAML frontmatter, or pure YAML
- No raw JSON or plain text deliverables
- No markdown inside ticket `task_steps` fields
- Log every tool call and result to `logs/session_<date>.jsonl`
