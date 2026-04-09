---
title: Audit Trail and Memory Policy
version: "2.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Audit Trail and Memory Policy

> **Medical Data Notice**: This system processes MUMPS source code from clinical
> information systems (VistA/EHR). The audit trail is a functional requirement,
> not a developer convenience. The journal is never truncated, rotated, or overwritten.
> All three layers must be written correctly on every execution.

Three distinct memory layers. Each has a strict scope. Do not conflate them.

---

## Layer 1 — JSONL Journal (Immutable Audit Trail)

`logs/luffy-journal.jsonl` — append-only, never overwrite, never truncate.

Every action that reads or transforms clinical source code emits two journal events:
one `pending` before the action and one `ok/error/pass/fail` after.
No batching. No deferred writes. Write before acting, write after.

### Session Bootstrap

1. Generate UUID → write to `logs/.session` (single line)
2. Emit `SESSION_START`:

```json
{"ts":"<ISO8601>","session":"<UUID>","executor":"<model_tag_from_settings>","event":"SESSION_START","stage":"<agent.stage>"}
```

If `model_tag` is absent from settings, write `"executor":"unspecified"`.
Never omit the `executor` field. It is required for audit traceability.

### Required Event Types

| Event | When |
|---|---|
| `SESSION_START` | Boot, before first ticket |
| `TICKET_START` | Ticket selected, moved to `in_progress/` |
| `TOOL_CALL` | Before AND after every tool invocation |
| `GATE_RUN` | Before AND after every gate execution |
| `TICKET_CLOSED` | Gate passes, ticket moved to `closed/` |
| `TICKET_RETRY` | Gate fails, attempts remaining |
| `TICKET_FAILED` | Gate fails, max_retries exhausted |
| `QUERY_RESPONSE` | Operator query answered (QUERY intent) |
| `SESSION_END` | Stack done, blocked, escalated, or operator halt |

### Event Schemas

**TICKET_START**
```json
{"ts":"","session":"","executor":"","event":"TICKET_START",
 "ticket":"","attempt":1,"deps_satisfied":true}
```

**TOOL_CALL (before)**
```json
{"ts":"","session":"","executor":"","event":"TOOL_CALL",
 "ticket":"","tool":"","args":{},"status":"pending"}
```

**TOOL_CALL (after — success)**
```json
{"ts":"","session":"","executor":"","event":"TOOL_CALL",
 "ticket":"","tool":"","status":"ok","elapsed_ms":0}
```

**TOOL_CALL (after — error)**
```json
{"ts":"","session":"","executor":"","event":"TOOL_CALL",
 "ticket":"","tool":"","status":"error","elapsed_ms":0,
 "error":"<one-line message>"}
```

**GATE_RUN (before)**
```json
{"ts":"","session":"","executor":"","event":"GATE_RUN",
 "ticket":"","command":"","status":"pending"}
```

**GATE_RUN (after)**
```json
{"ts":"","session":"","executor":"","event":"GATE_RUN",
 "ticket":"","command":"","exit_code":0,"elapsed_ms":0,
 "status":"pass"}
```
Use `"status":"fail"` for non-zero exit.

**TICKET_CLOSED**
```json
{"ts":"","session":"","executor":"","event":"TICKET_CLOSED",
 "ticket":"","attempt":1,"wall_sec":0.0,
 "tokens_in":null,"tokens_out":null}
```
Write `null` for token counts if unavailable. Never omit the fields.

**TICKET_RETRY**
```json
{"ts":"","session":"","executor":"","event":"TICKET_RETRY",
 "ticket":"","attempt":1,"gate_exit_code":1,
 "reason":"<one line from gate stderr>"}
```

**TICKET_FAILED**
```json
{"ts":"","session":"","executor":"","event":"TICKET_FAILED",
 "ticket":"","attempts":2,"gate_exit_code":1,
 "reason":"<one line from gate stderr>",
 "scratch_path":"logs/scratch-<id>-FAILED.jsonl"}
```

**QUERY_RESPONSE**
```json
{"ts":"","session":"","executor":"","event":"QUERY_RESPONSE",
 "query_text":"<verbatim operator input>",
 "response_summary":"<one-line description of what was returned>"}
```

**SESSION_END**
```json
{"ts":"","session":"","executor":"","event":"SESSION_END",
 "reason":"DONE",
 "tickets_closed":0,"tickets_failed":0,"wall_sec":0.0}
```
Reason: `DONE` | `BLOCKED` | `ESCALATED` | `OPERATOR_HALT`

---

## Layer 2 — Scratchpad (Per-Ticket Working Memory)

The scratchpad is the bot's problem-solving surface for a single ticket.
It is written to disk — not internal monologue, not conversation history.
Format depends on `agent.stage` (see `07-stack-runner.md`).

### JSONL Scratch File (stage: bud / branch)

File: `logs/scratch-{ticket_id}.jsonl`

Emit one JSON event per meaningful action:
- `SCRATCH_INIT` at creation
- `STEP_START` per task_step (before reasoning begins)
- `REASONING` per task_step (mandatory — first-principles chain output, see below)
- `TOOL_CALL pending/ok/error` mirroring journal (local detail)
- `VERIFY` per task_step (mandatory — expected vs actual comparison, see below)
- `STEP_DONE` per task_step (after verification passes)
- `ANOMALY` for anything unexpected: format deviations, unexpected AST shapes,
  missing context files, non-deterministic tool output
- `GATE_RUN pass/fail`
- `SCRATCH_CLOSE result: CLOSED/FAILED`

**Anomaly events are critical for SOTA failure analysis.**
Every anomaly must include `location` (file:line if applicable) and `note`.
Anomaly examples for MUMPS translation:
- `{"event":"ANOMALY","location":"MPIF001.m:142","note":"^TMP($J) write — classify as PROC_LOCAL not GLOBAL"}`
- `{"event":"ANOMALY","location":"MPIF001.m:88","note":"LOCK +^AUPNVDT(DFN) with no matching LOCK - — may be unconditional"}`
- `{"event":"ANOMALY","location":"parse_mumps.py:output","note":"AST node 'indirection' found — no handler in emit_python_stub.py"}`

### Mandatory Reasoning Events

Every task_step MUST produce a `REASONING` event before the tool call and a `VERIFY`
event after. These are not optional annotations — they are structural requirements
enforced at the gate.

**REASONING event schema:**
```jsonl
{"ts":"<ISO8601>","ticket":"<ID>","event":"REASONING","step":<n>,
 "decomposition":"<smallest falsifiable sub-claim from step 1 of 00-policy.md>",
 "ground_truth":"<evidence-based facts from step 2>",
 "constraints":"<immutable boundaries from step 3>",
 "minimal_transform":"<smallest satisfying change from step 4>"}
```

- `decomposition`: What is the minimum unit of work that can be independently verified?
- `ground_truth`: What do we know from AST output, file contents, and tool results — not assumptions?
- `constraints`: MUMPS source is read-only, output schema is fixed, tools are limited to allowed_tools.
- `minimal_transform`: Given the above, what is the single smallest action that satisfies the criteria?

**VERIFY event schema:**
```jsonl
{"ts":"<ISO8601>","ticket":"<ID>","event":"VERIFY","step":<n>,
 "expected":"<what the acceptance criteria requires for this step>",
 "actual":"<what the tool actually produced — file path, content hash, or summary>",
 "pass":<true|false>}
```

If `pass` is false, the executor MUST return to the REASONING step with updated
analysis before retrying. Blind retries without updated reasoning are a protocol violation.

**Gate enforcement:** Before running `gate_command`, the executor validates the scratch
file. If any executed task_step lacks a REASONING + VERIFY pair, the gate is
automatically failed with reason `"scratch validation: missing REASONING/VERIFY for step N"`.
This is checked BEFORE the acceptance test runs — a missing scratch event means the
gate never executes.

### On Retry

1. Read existing scratch JSONL
2. Emit `{"event":"RETRY","attempt":<n>,"reason":"<gate failure one-liner>"}`
3. Re-execute only failed steps

### On Close

- `TICKET_CLOSED`: delete `logs/scratch-{ticket_id}.jsonl`
- `TICKET_FAILED`: rename to `logs/scratch-{ticket_id}-FAILED.jsonl` — **never delete**

---

## Layer 3 — Living Documents (Cross-Session Knowledge)

Living docs survive session boundaries. Human-readable summary layer.
Write only on `TICKET_FAILED` or final `SESSION_END`. Not on every ticket close.

### TROUBLESHOOTING.md — Failure Log (Append Only)

```markdown
## {ticket_id} — {ISO8601 date}

**Executor**: {model_tag}  
**Session**: {UUID}  
**Attempts**: {n}  
**Gate command**: `{gate_command}`  
**Gate output** (truncated to 40 lines):
```
{exact stdout/stderr}
```
**Anomaly log** (from scratch JSONL):
{paste all ANOMALY events, formatted as bullet list}

**Status**: ESCALATED — awaiting human review
```

### REPLICATION-NOTES.md — Success Log (Append Only)

```markdown
## Session {UUID} — {ISO8601 date}

**Executor**: {model_tag}  
**Stack**: {routine or project name}  
**Tickets closed**: {n}  
**Tickets failed**: {n}  
**Wall time**: {wall_sec}s  
**Output artifacts**: {comma-separated result_path values}  
```

### ISSUE.md — Active Escalation (Overwrite on Each New Failure)

```yaml
---
id: ESCALATED-{ticket_id}
date: <ISO8601>
session: <UUID>
executor: <model_tag>
blocked_ticket: <ticket_id>
attempts: <n>
gate_command: "<gate_command>"
gate_exit_code: <n>
gate_output: |
  <exact output, max 20 lines>
anomaly_log: |
  <all ANOMALY events from scratch JSONL>
recommended_action: "Human review required. See TROUBLESHOOTING.md and scratch JSONL."
---
```

---

## Journal Integrity Rules

1. **Never truncate** `logs/luffy-journal.jsonl` — ever
2. **Never overwrite** any journal line — ever
3. If a write to journal fails → halt immediately, report to operator, do not continue
4. Journal must be parseable as JSONL (one valid JSON object per line, newline-terminated)
5. `ts` fields must be ISO8601 UTC (e.g. `2026-04-09T12:00:00.000Z`)
6. `session` UUID must match `logs/.session` for the entire session
7. `executor` field must be consistent within a session — read once from settings at boot

---

## Halt Policy

After writing living docs on `TICKET_FAILED`:
- Emit `SESSION_END reason: ESCALATED`
- STOP. Leave `tickets/failed/` intact.
- Do not proceed to any other ticket.

Valid SESSION_END reasons and only these:
1. `tickets/open/` empty → `DONE`
2. Open tickets, none ready → `BLOCKED`
3. Any ticket hits max_retries → `ESCALATED`
4. Operator sends stop signal → `OPERATOR_HALT`
