---
title: Audit Trail and Memory Policy (Luffy Law)
version: "1.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Audit Trail and Memory Policy

This policy defines three distinct memory layers. Each layer has a strict scope.
Do not conflate them. Do not skip any layer.

---

## Layer 1 — JSONL Journal (Immutable Audit Trail)

Every action emits one JSON line to `logs/journal.jsonl`. Append-only. Never overwrite.

### Session Bootstrap

At session start, before any ticket work:
1. Generate a UUID session identifier
2. Write it to `logs/.session` (single line, no newline)
3. Emit one `SESSION_START` event:

```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","event":"SESSION_START"}
```

MODEL_TAG is read from `settings.yaml` executor section if present, otherwise write `"unknown"`.

### Required Event Types

Emit these events at the exact moments described. No batching.

| Event | When to Emit |
|---|---|
| `SESSION_START` | Session boot, before first ticket |
| `TICKET_START` | When a ticket is selected and moved to `in_progress/` |
| `TOOL_CALL` | Before AND after every tool invocation |
| `GATE_RUN` | Before AND after every `gate_command` execution |
| `TICKET_CLOSED` | When gate passes and ticket moves to `closed/` |
| `TICKET_RETRY` | When gate fails but `attempts < max_retries` |
| `TICKET_FAILED` | When gate fails and `attempts >= max_retries` |
| `SESSION_END` | When stack is exhausted, blocked, or escalated |

### Event Schemas

**TICKET_START**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TICKET_START","attempt":<n>,"deps_satisfied":true}
```

**TOOL_CALL (before)**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TOOL_CALL","tool":"<name>","args":{},"status":"pending"}
```

**TOOL_CALL (after)**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TOOL_CALL","tool":"<name>","status":"ok","elapsed_ms":<n>}
```
Use `"status":"error"` and add `"error":"<message>"` if the tool returns non-zero or throws.

**GATE_RUN (before)**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"GATE_RUN","command":"<gate_command>","status":"pending"}
```

**GATE_RUN (after)**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"GATE_RUN","command":"<gate_command>","exit_code":<n>,"elapsed_ms":<n>,"status":"pass"}
```
Use `"status":"fail"` for non-zero exit.

**TICKET_CLOSED**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TICKET_CLOSED","attempt":<n>,"wall_sec":<float>,"tokens_in":<n>,"tokens_out":<n>}
```
If token counts are unavailable, write `null`.

**TICKET_RETRY**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TICKET_RETRY","attempt":<n>,"gate_exit_code":<n>,"reason":"<one line from gate output>"}
```

**TICKET_FAILED**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","ticket":"<ID>","event":"TICKET_FAILED","attempts":<n>,"gate_exit_code":<n>,"reason":"<one line from gate output>"}
```

**SESSION_END**
```json
{"ts":"<ISO8601>","session":"<UUID>","model":"<MODEL_TAG>","event":"SESSION_END","reason":"DONE","tickets_closed":<n>,"tickets_failed":<n>,"wall_sec":<float>}
```
Reason is one of: `DONE` | `BLOCKED` | `ESCALATED`

---

## Layer 2 — Scratchpad (Per-Ticket Working Memory)

The scratchpad is the bot's short-term problem-solving surface for a single ticket.
It is a Markdown file on disk — not internal monologue, not conversation history.
The bot writes it, re-reads it during retries, and deletes or archives it on ticket close.

### Creation

At `TICKET_START`, create `logs/scratch-{ticket_id}.md`:

```markdown
# {ticket_id} Working Scratch — attempt {n}

## Goal
{ticket title verbatim}

## Context Evidence
<!-- Key facts extracted from context_files and prior ticket outputs -->
<!-- e.g. entry_point count, global patterns, dependency outputs -->

## Steps
<!-- One checkbox per task_step from the ticket YAML -->
- [ ] {step 1}
- [ ] {step 2}
...

## Anomaly Log
<!-- Append observations here as they occur. Format: line/location: observation -->
```

### During Execution

- Check off each step as it completes: `- [x]`
- Append anomalies immediately when observed — do not defer
- Anomaly format: `- {location}: {observation}` (e.g. `- Line 142: ^TMP($J) write — classify as PROC_LOCAL`)

### On Retry

Before re-executing task_steps:
1. Read the scratch file
2. Update the header: `attempt {n}` → `attempt {n+1}`
3. Uncheck only the steps that need to be redone
4. Note the retry reason under Anomaly Log

### On Close

- `TICKET_CLOSED`: delete `logs/scratch-{ticket_id}.md`
- `TICKET_FAILED`: rename to `logs/scratch-{ticket_id}-FAILED.md` — preserve for audit

---

## Layer 3 — Living Documents (Cross-Session Knowledge)

Living docs survive session boundaries. They are the human-readable summary layer
and the recovery surface for the next session or operator.

Write to living docs **only** on `TICKET_FAILED` or final `SESSION_END`.
Do not write on every ticket close — that creates noise.

### TROUBLESHOOTING.md — Failure Log (Append Only)

On `TICKET_FAILED`, append this block:

```markdown
## {ticket_id} — {ISO8601 date}

**Model**: {MODEL_TAG}  
**Session**: {UUID}  
**Attempts**: {n}  
**Gate command**: `{gate_command}`  
**Gate output**:
```
{exact stdout/stderr from gate_command, truncated to 40 lines}
```
**Root cause hypothesis** (from scratch anomaly log):  
{paste anomaly log entries}

**Status**: ESCALATED — awaiting human review
```

### REPLICATION-NOTES.md — Success Log (Append Only)

On `SESSION_END` with reason `DONE`, append:

```markdown
## Session {UUID} — {ISO8601 date}

**Model**: {MODEL_TAG}  
**Stack**: {routine name, e.g. MPIF001}  
**Tickets closed**: {n}  
**Tickets failed**: {n}  
**Wall time**: {wall_sec}s  
**Output artifacts**: {comma-separated list of result_path values from closed tickets}  
```

### ISSUE.md — Escalation Block (Overwrite on Failure)

On `TICKET_FAILED`, overwrite `ISSUE.md` with:

```yaml
---
id: ESCALATED-{ticket_id}
date: <ISO8601>
session: <UUID>
model: <MODEL_TAG>
blocked_ticket: <ticket_id>
attempts: <n>
gate_command: "<gate_command>"
gate_exit_code: <n>
gate_output: |
  <exact output, max 20 lines>
root_cause_hypothesis: |
  <from scratch anomaly log>
recommended_action: "Human review required — see TROUBLESHOOTING.md"
---
```

---

## Halt Policy

After writing living docs on `TICKET_FAILED`:
- Emit `SESSION_END` with `reason: ESCALATED` to journal
- STOP. Do not proceed to the next ticket.
- Leave `tickets/failed/` intact for inspection.

The only valid states for stopping the loop:
1. `tickets/open/` is empty → `SESSION_END reason: DONE`
2. All remaining open tickets have unsatisfied `depends_on` → `SESSION_END reason: BLOCKED`
3. Any ticket hits `max_retries` → `SESSION_END reason: ESCALATED`
