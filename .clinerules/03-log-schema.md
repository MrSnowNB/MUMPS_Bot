# Audit Log Schema

Every action appends one JSON line to `logs/luffy-journal.jsonl`.
The file is append-only. Never truncate or overwrite.

## Event Types

### HARNESS_RESET
```json
{"event":"HARNESS_RESET","ts":"ISO-8601","operator":"string","note":"string"}
```

### TICKET_START
```json
{
  "event": "TICKET_START",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "title": "string",
  "retry_count": 0
}
```

### TOOL_CALL
```json
{
  "event": "TOOL_CALL",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "step": 1,
  "tool": "parse_mumps",
  "input_hash": "sha256:...",
  "input_summary": "MPIF001.m → output/MPIF001-ast.json"
}
```

### TOOL_RESULT
```json
{
  "event": "TOOL_RESULT",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "step": 1,
  "tool": "parse_mumps",
  "status": "ok",
  "output_path": "output/MPIF001-ast.json",
  "output_hash": "sha256:...",
  "duration_ms": 412
}
```

### ACCEPTANCE_CHECK
```json
{
  "event": "ACCEPTANCE_CHECK",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "criterion_id": "AC-01",
  "test": "python -c \"import json; d=json.load(open('output/MPIF001-ast.json')); assert d['tree']['type']=='program'\"",
  "result": "PASS"
}
```

### TICKET_CLOSED
```json
{
  "event": "TICKET_CLOSED",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "artifacts": ["output/MPIF001-ast.json"],
  "criteria_passed": ["AC-01", "AC-02"]
}
```

### TICKET_FAILED
```json
{
  "event": "TICKET_FAILED",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "retry_count": 1,
  "failure_reason": "string",
  "criterion_failed": "AC-02"
}
```

### TICKET_BLOCKED
```json
{
  "event": "TICKET_BLOCKED",
  "ts": "ISO-8601",
  "ticket_id": "MUM-T01",
  "retry_count": 3,
  "escalation_note": "string — describe what needs human decision"
}
```

## Integrity Check

To verify log integrity at any time:
```bash
python scripts/verify_log.py logs/luffy-journal.jsonl
```
This script checks: valid JSON on every line, monotonic timestamps,
no gaps in step sequences per ticket, all referenced output files exist.
