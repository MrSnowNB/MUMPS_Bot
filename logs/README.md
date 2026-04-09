# logs/

There is **one** audit log: `luffy-journal.jsonl`.

All other files in this directory (`journal.jsonl`, `journal.md`) are stale artifacts
from prior scaffolding runs. They are kept as empty placeholders but **must not be
written to**. Only `luffy-journal.jsonl` is authoritative.

## Why one log?

Two parallel logs create an audit split-brain: if Cline writes to one and a script
reads from another, integrity checks silently pass on an incomplete view. One file,
one truth.

## Schema

```json
{
  "event": "HARNESS_RESET | TICKET_START | TOOL_CALL | TOOL_RESULT | ACCEPTANCE_CHECK | TICKET_CLOSED | TICKET_FAILED | TICKET_BLOCKED",
  "ts": "ISO-8601 UTC e.g. 2026-04-09T13:00:00Z",
  "ticket_id": "MUM-T01",
  "tool": "parse_mumps",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "output_path": "output/MPIF001-ast.json",
  "status": "ok | error",
  "detail": "freeform"
}
```

## Rules
- **Append only.** Never truncate or overwrite.
- A `HARNESS_RESET` event marks the start of a new run epoch.
- Cross-check `output_hash` against `output/` files using `scripts/verify_log.py`.

## Verify
```bash
python scripts/verify_log.py logs/luffy-journal.jsonl
```
