---
title: Failure Handling Procedure
version: "3.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Failure Handling Procedure

## When to Trigger

Trigger the full failure procedure on **any** of:
- A validation gate returns non-green output
- An unhandled exception occurs during task execution
- The agent is uncertain about the correct next action
- A file format violation is detected
- A phase transition condition is not met
- The executor returns an empty or malformed response after all retries exhausted
- A tool call returns `ERROR:` and the error is not self-evidently fixable in one step

## Procedure (Ordered — Do Not Skip Steps)

### Step 1: Capture Logs

```
Save full stdout/stderr to logs/ directory.
Filename format: logs/ISS-<YYYY-MM-DD>-<short-description>.log
Do not truncate. Save verbatim.
```

### Step 2: Update TROUBLESHOOTING.md

Append a new `TS-XXX` entry:
- Context, Symptom, Error Snippet, Probable Cause, Quick Fix, Permanent Fix, Prevention
- If the issue matches an existing entry, add a `recurrence` sub-field — no duplicates.

### Step 3: Update REPLICATION-NOTES.md

Append to the **Recurring Errors** table and, if the environment changed,
add a row to **Environment Deltas**.

### Step 4: Open ISSUE.md

Create a new `ISS-XXX` entry with:
- `status: open`
- `blocked_on: human`
- The exact requested human action spelled out clearly

### Step 5: halt_and_wait_human

Stop all work. Do not make further file changes, run commands, or attempt self-recovery.
Inform the human: "Halted on ISS-XXX. See ISSUE.md for required action."

## Prohibited Actions After Halt

- **No autonomous executor switching:** If the execution environment fails, do NOT modify
  `settings.yaml` or any config to switch execution targets. Halt and wait.
- **No downloading fixes:** Never execute remote scripts to reinstall or fix a broken service.
- No retries without human instruction
- No speculative fixes
- No modifications to files outside living docs during halt state
- No advancing to the next lifecycle phase

## Retry Budget

Before triggering full failure procedure, the executor is permitted:
- **max_retries: 2** — two attempts on the same ticket
- On attempt 2 failure: trigger full procedure above, set ticket status `FAILED`
- The human must explicitly set the ticket back to `OPEN` to allow retry
