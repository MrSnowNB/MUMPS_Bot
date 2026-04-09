# tickets/

Ticket lifecycle directories for the Guardian Harness.

## State Machine

```
OPEN → IN_PROGRESS → CLOSED
                  ↘ FAILED (retry ≤3) → OPEN
                            (retry >3) → BLOCKED (escalate)
```

## Directories

| Dir | Meaning |
|-----|---------|
| `open/` | Ready to run (all deps CLOSED) |
| `in_progress/` | Cline is actively executing |
| `closed/` | Acceptance criteria passed |
| `failed/` | Last run failed; retry pending |

## Ticket Families

| Prefix | Family | Count |
|--------|--------|-------|
| `MUM-T*` | MPIF001 MUMPS parse + translate | 11 |
| `BUILD-T*` | Docker + Ollama environment | 7 |
| `ROOK-T*` | Executor loop + ticket runner | 7 |
| `HARN-T*` | Cline harness + audit wiring | 3 |

## Reset Procedure

To reset all tickets to OPEN:
1. Move all files from `closed/`, `failed/`, `in_progress/` back to `open/`
2. Append a `HARNESS_RESET` event to `logs/luffy-journal.jsonl`
3. Commit with message: `chore: reset tickets → all OPEN`

## Running the First Ticket

Open `tickets/open/MUM-T01.yaml` in Cline and say:
> "Execute this ticket. Follow the task_steps exactly. Use only allowed_tools. Log every action to logs/luffy-journal.jsonl."
