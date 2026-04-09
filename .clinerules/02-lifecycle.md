---
title: Task Lifecycle and Gating
version: "2.0"
scope: global
applies_to: orchestrator
last_updated: "2026-04-09"
---

# Task Lifecycle and Gating

## Sequential Phase Enforcement

The agent enforces a strict linear lifecycle. Phases are non-reentrant without human instruction.

### Phase: Plan

- Human defines task scope in `SPEC.md`
- Agent reads spec, asks clarifying questions if ambiguous
- Agent may NOT write code, run commands, or modify any file outside `SPEC.md` and `PLAN.md`
  during this phase
- **Exit gate**: Human explicitly approves the plan in writing

### Phase: Build

- Agent implements exactly what is described in the approved spec
- All new files must comply with the file format policy (`01-file-format.md`)
- Agent commits atomically — one logical change per commit
- If the implementation diverges from the spec for any reason, agent must **stop and update
  SPEC.md**, then wait for re-approval
- **Exit gate**: All four validation gates green (see `00-policy.md`)

### Phase: Validate

- Agent runs all four gate commands in order: unit → lint → type → docs
- Any non-green gate triggers immediate failure handling
- Agent does not attempt to fix failures autonomously beyond a single obvious correction
  (e.g., a missing import)
- **Exit gate**: Human reviews gate output and approves progression

### Phase: Review

- Human reviews the diff
- Agent answers questions, makes **only requested changes**
- No speculative improvements during review
- **Exit gate**: Human approves merge/release

### Phase: Release

- Agent tags the release, updates `REPLICATION-NOTES.md` with the release summary
- Artifacts documented with version, date, and checksum where applicable

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
