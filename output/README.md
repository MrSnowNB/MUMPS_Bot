# output/

All artifacts produced by ticket execution land here.

## Naming Convention

| Artifact | Pattern | Produced by |
|----------|---------|-------------|
| Raw AST JSON | `{ROUTINE}-ast.json` | MUM-T01 (parse_mumps) |
| Entry point list | `{ROUTINE}-entries.json` | MUM-T02 (list_entry_points) |
| Global access map | `{ROUTINE}-globals.json` | MUM-T03 (extract_globals) |
| Call graph | `{ROUTINE}-calls.json` | MUM-T04 (extract_calls) |
| AST query results | `{ROUTINE}-query-{label}.json` | MUM-T05 (query_ast) |
| Routine summary | `{ROUTINE}-summary.json` | MUM-T06 (summarize_routine) |
| Python stubs | `{ROUTINE}.py` | MUM-T07 (emit_python_stub) |
| Test file | `test_{ROUTINE}.py` | MUM-T08 |
| ATA document | `{ROUTINE}-ATA.md` | MUM-T11 |

## Integrity

Every file written here must have a corresponding `TOOL_RESULT` entry in
`logs/luffy-journal.jsonl` with matching `output_hash` (SHA-256).
