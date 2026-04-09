# logs/

All Cline execution events are appended to `luffy-journal.jsonl` as newline-delimited JSON.

## Schema

```json
{
  "event": "TICKET_START | TOOL_CALL | TOOL_RESULT | TICKET_CLOSED | TICKET_FAILED | TICKET_BLOCKED | HARNESS_RESET",
  "ts": "ISO-8601 timestamp",
  "ticket_id": "MUM-T01",
  "tool": "parse_mumps | list_entry_points | ...",
  "input_hash": "sha256 of tool input",
  "output_hash": "sha256 of tool output",
  "status": "ok | error",
  "detail": "freeform string"
}
```

## Rules
- **Never delete** `luffy-journal.jsonl` during a run — append only.
- A `HARNESS_RESET` event marks the start of a new run. Everything before it is a prior audit epoch.
- All `output/` artifacts are referenced by filename; cross-check hashes here for tamper detection.
