---
title: Stack Execution and YOLO Loop Policy
version: "2.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Stack Execution and YOLO Loop Policy

This rule governs autonomous ticket stack traversal.
Rook is the loop controller. No external runner script is required.

---

## YOLO Mode Override

When the operator sends an EXECUTE intent (`Begin`, `Run the stack`, etc.),
all human approval gates from `03-lifecycle.md` are SUSPENDED for the duration
of the session. Rook runs the full ticket stack without asking for confirmation
between phases or tickets.

All other policy rules remain active, especially:
- The audit mandate (09-audit.md)
- The failure halt mandate (00-policy.md)
- Tool restrictions per ticket `allowed_tools`

---

## Session Start Sequence

1. Read `.clinerules/` in filename order (00 → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11)
2. Read `settings.yaml` — executor config, ticket dirs, max_retries, model_tag
3. Generate session UUID → write to `logs/.session`
4. Emit `SESSION_START` to `logs/luffy-journal.jsonl`
5. Enter the execution loop

---

## Execution Loop

Repeat until a stop condition is met:

### Step 1 — Find Ready Tickets

Scan `tickets/open/`. A ticket is **ready** if:
- `depends_on` is empty, OR
- Every ticket ID in `depends_on` exists as a file in `tickets/closed/`

If no tickets are ready:
- `tickets/open/` is empty → `SESSION_END reason: DONE`
- Open tickets exist but none ready → `SESSION_END reason: BLOCKED`

### Step 2 — Select Ticket

Lowest lexicographic ID among ready tickets (HARNESS-T01 before MUM-T01, MUM-T01 before MUM-T02).

### Step 3 — Start Ticket

1. Move YAML: `open/` → `in_progress/`
2. Increment `attempts` in the YAML, write back
3. Emit `TICKET_START` to journal
4. Create scratch file (see `09-audit.md` Layer 2)

### Step 4 — Execute Task Steps

For each step in `task_steps`:

1. Emit `STEP_START` to scratch file
2. **Emit `REASONING` event to scratch file** — apply the 5-step first-principles chain
   from `00-policy.md`. Document decomposition, ground truth, constraints, and minimal
   transformation. This is mandatory for every step, not just complex ones.
3. Emit `TOOL_CALL pending` to journal AND scratch
4. Execute using only tools in `allowed_tools`
5. Emit `TOOL_CALL ok/error` to journal AND scratch with `elapsed_ms`
6. **Emit `VERIFY` event to scratch file** — compare expected vs actual output, record pass/fail
7. Log anomalies to scratch immediately (ANOMALY events)
8. Emit `STEP_DONE` to scratch file

Do not skip steps. Do not reorder steps. Do not add unlisted steps.
Every step MUST have both a REASONING and VERIFY event in the scratch file.

### Step 5 — Run Gate

0. **Validate scratch file integrity.**
   Read `logs/scratch-{ticket_id}.jsonl`. Verify:
   - File exists and is valid JSONL
   - Contains `SCRATCH_INIT`
   - For each task_step index that was executed: at least one `REASONING` event
     and one `VERIFY` event with `"pass": true`
   If validation fails → treat as gate failure. Emit `GATE_RUN fail` with
   `reason: "scratch incomplete: missing REASONING/VERIFY for step(s) N"`.
   Proceed to the gate-fail handling path (retry or escalate).

1. Emit `GATE_RUN pending` to journal
2. Execute `gate_command` via shell
3. Emit `GATE_RUN pass/fail` to journal with `exit_code` and `elapsed_ms`

**Gate passes (exit 0):**
- Move YAML: `in_progress/` → `closed/`
- Emit `TICKET_CLOSED` to journal
- Delete scratch file
- **Return immediately to Step 1. No chat output. No confirmation request.**

**Gate fails, `attempts < max_retries`:**
- Emit `TICKET_RETRY` to journal with reason
- Move YAML: `in_progress/` → `open/`
- Re-read scratch file
- Return to Step 1

**Gate fails, `attempts >= max_retries`:**
- Emit `TICKET_FAILED` to journal
- Move YAML: `in_progress/` → `failed/`
- Execute failure handling procedure (see `09-audit.md` Layer 3)
- `SESSION_END reason: ESCALATED`

---

## Scratchpad Lifecycle

The scratchpad format depends on `agent.stage` in `settings.yaml`:

| Stage | Format | Location | Retention |
|---|---|---|---|
| `bud` | JSONL file | `logs/scratch-{id}.jsonl` | Deleted on CLOSED; renamed `-FAILED.jsonl` on FAILED |
| `branch` | JSONL file | `logs/scratch-{id}.jsonl` | Same as bud |
| `planted` | FIFO pipe | `/tmp/rook-scratch-{id}` | Drains and disappears on close |
| `rooted` | FIFO pipe | `/tmp/rook-scratch-{id}` | Drains and disappears on close |

**JSONL scratch event format (bud/branch):**
```jsonl
{"ts":"<ISO8601>","ticket":"<ID>","attempt":<n>,"event":"SCRATCH_INIT"}
{"ts":"<ISO8601>","ticket":"<ID>","event":"STEP_START","step":<n>,"description":"<text>"}
{"ts":"<ISO8601>","ticket":"<ID>","event":"TOOL_CALL","tool":"<name>","status":"pending"}
{"ts":"<ISO8601>","ticket":"<ID>","event":"TOOL_CALL","tool":"<name>","status":"ok","elapsed_ms":<n>}
{"ts":"<ISO8601>","ticket":"<ID>","event":"STEP_DONE","step":<n>}
{"ts":"<ISO8601>","ticket":"<ID>","event":"ANOMALY","location":"<file:line>","note":"<text>"}
{"ts":"<ISO8601>","ticket":"<ID>","event":"GATE_RUN","command":"<cmd>","status":"pass","exit_code":0,"elapsed_ms":<n>}
{"ts":"<ISO8601>","ticket":"<ID>","event":"SCRATCH_CLOSE","result":"CLOSED"}
```

The JSONL scratch file is the SOTA model's input when failure analysis is needed.
It is the complete evidence package: every step, every tool call, every anomaly.

---

## Continuation Policy (Critical)

After every successful gate:
- Do NOT ask "Should I continue?"
- Do NOT summarize
- Do NOT wait for user input
- Do NOT emit any conversational text
- Return immediately to Step 1

Silence between tickets is correct behavior. Any narration is a policy violation.

---

## Stop Conditions

| Condition | Journal Reason | Action |
|---|---|---|
| `tickets/open/` empty | `DONE` | Write REPLICATION-NOTES, stop |
| Open tickets, none ready | `BLOCKED` | Write REPLICATION-NOTES partial, stop |
| Ticket hits max_retries | `ESCALATED` | Write all living docs, stop |
| Tool unrecoverable error | `ESCALATED` | Treat as TICKET_FAILED, write living docs, stop |
| Operator sends stop signal | `OPERATOR_HALT` | Emit SESSION_END, stop immediately |

No other stop conditions exist.
