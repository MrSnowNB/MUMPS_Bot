---
title: Stack Execution and YOLO Loop Policy
version: "1.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Stack Execution and YOLO Loop Policy

This rule governs autonomous ticket stack traversal.
The bot is the loop controller. No external runner script is required.

---

## Session Start Sequence

1. Read `.clinerules/` — all rules are active for this session
2. Read `settings.yaml` — load executor config, ticket dirs, max_retries
3. Execute session bootstrap (see `06-audit.md` Layer 1)
4. Begin the execution loop

---

## Execution Loop

Repeat until a stop condition is met:

### Step 1 — Find Ready Tickets

Scan `tickets/open/`. A ticket is **ready** if:
- Its `depends_on` list is empty, OR
- Every ticket ID in `depends_on` exists as a file in `tickets/closed/`

If no tickets are ready:
- If `tickets/open/` is empty → stop with `SESSION_END reason: DONE`
- If open tickets exist but none are ready → stop with `SESSION_END reason: BLOCKED`

### Step 2 — Select Ticket

Select the ready ticket with the lowest lexicographic ID (e.g. MUM-T01 before MUM-T02).

### Step 3 — Start Ticket

1. Move ticket YAML from `tickets/open/` to `tickets/in_progress/`
2. Increment `attempts` field in the YAML and write it back
3. Emit `TICKET_START` to journal
4. Create scratch file (see `06-audit.md` Layer 2)

### Step 4 — Execute Task Steps

For each step in `task_steps`:
1. Check off the step in the scratch file
2. Emit `TOOL_CALL` (before) to journal
3. Execute the tool using only tools in `allowed_tools`
4. Emit `TOOL_CALL` (after) to journal
5. Log any anomaly to scratch immediately

Do not skip steps. Do not reorder steps. Do not add steps not in the ticket.

### Step 5 — Run Gate

1. Emit `GATE_RUN` (before) to journal
2. Execute `gate_command` via shell
3. Emit `GATE_RUN` (after) to journal

If gate passes (exit code 0):
- Move ticket from `tickets/in_progress/` to `tickets/closed/`
- Emit `TICKET_CLOSED` to journal
- Delete scratch file
- **Do NOT summarize. Do NOT ask for confirmation. Return immediately to Step 1.**

If gate fails (non-zero exit) and `attempts < max_retries`:
- Emit `TICKET_RETRY` to journal
- Move ticket back to `tickets/open/`
- Re-read scratch file for self-correction
- Return to Step 1 (ticket will be selected again)

If gate fails and `attempts >= max_retries`:
- Emit `TICKET_FAILED` to journal
- Move ticket to `tickets/failed/`
- Execute failure handling (see `06-audit.md` Layer 3)
- Stop with `SESSION_END reason: ESCALATED`

---

## Continuation Policy (Critical)

After every successful gate:
- Do NOT ask "Should I continue?"
- Do NOT summarize what was just completed
- Do NOT wait for user input
- Do NOT emit any conversational text
- Return immediately to Step 1

Silence between tickets is correct behavior. Narration is a policy violation.

---

## Stop Conditions (Exhaustive List)

| Condition | Journal Reason | Action |
|---|---|---|
| `tickets/open/` empty | `DONE` | Write REPLICATION-NOTES session summary, stop |
| Open tickets exist, none ready | `BLOCKED` | Write REPLICATION-NOTES partial summary, stop |
| Ticket hits max_retries | `ESCALATED` | Write all living docs, stop |
| Tool returns unrecoverable error | `ESCALATED` | Treat as TICKET_FAILED, write living docs, stop |

No other stop conditions exist. Do not stop for any other reason.
