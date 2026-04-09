---
title: Task Lifecycle and Gating
version: "2.1"
scope: global
applies_to: orchestrator
last_updated: "2026-04-09"
---

# Task Lifecycle and Gating

## YOLO Mode Override

> **When `07-stack-runner.md` is active (Rook session), the phase approval gates below
> are SUSPENDED. Rook runs the full ticket stack autonomously without human approval
> between phases. Human approval gates apply only to interactive planning sessions
> outside of the ticket stack runner.**

---

## Sequential Phase Enforcement

The agent enforces a strict linear lifecycle. Phases are non-reentrant without human instruction.

### Phase: Plan

- Human defines task scope in `SPEC.md`
- Agent reads spec, asks clarifying questions if ambiguous
- Agent may NOT write code, run commands, or modify any file outside `SPEC.md` and `PLAN.md`
  during this phase
- **Exit gate**: Human explicitly approves the plan in writing *(suspended in YOLO mode)*

### Phase: Build

- Agent implements exactly what is described in the approved spec
- All new files must comply with the file format policy (`01-file-format.md`)
- Agent commits atomically — one logical change per commit
- If the implementation diverges from the spec for any reason, agent must **stop and update
  SPEC.md**, then wait for re-approval *(suspended in YOLO mode — log to scratch instead)*
- **Exit gate**: All validation gates green *(in YOLO mode, gate = ticket gate_command)*

### Phase: Validate

- Agent runs gate commands in order
- Any non-green gate triggers immediate failure handling per `04-failure-handling.md`
- **Exit gate**: Human reviews gate output *(suspended in YOLO mode)*

### Phase: Review

- Human reviews the diff
- Agent answers questions, makes **only requested changes**
- No speculative improvements during review
- **Exit gate**: Human approves merge/release *(suspended in YOLO mode)*

### Phase: Release

- Agent tags the release, updates `REPLICATION-NOTES.md` with the release summary
- Artifacts documented with version, date, and checksum where applicable

---

## Ticket State Machine

Every ticket moves through these states in order. No skipping.

```
OPEN → IN_PROGRESS → CLOSED
                  ↘ FAILED  → (human resolves) → OPEN
                  ↘ BLOCKED → (dependency resolves) → OPEN
```

| State       | Who Sets It     | Meaning                                      |
|-------------|-----------------|----------------------------------------------|
| OPEN        | Planner         | Ready to execute; all deps CLOSED            |
| IN_PROGRESS | Executor        | Actively being worked                        |
| CLOSED      | Executor        | Acceptance criteria verified green           |
| FAILED      | Executor        | Gate failed after max_retries exhausted      |
| BLOCKED     | Executor/Human  | Cannot proceed; requires human or dep        |

A ticket may only be set to `IN_PROGRESS` if ALL `depends_on` tickets are `CLOSED`.
An executor must never hold more than one ticket `IN_PROGRESS` at a time.
