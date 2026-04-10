---
title: "MPIF001 Ticket DAG — Guardian Analysis Pipeline"
version: "1.0"
last_updated: "2026-04-09"
moved: "2026-04-09 — relocated from repo root to docs/ during recovery audit"
note: |
  This DAG spec describes the per-routine 11-ticket pattern for MPIF001.
  It is preserved as a reference template for VISTA-T01 and subsequent routines.
  The authoritative execution order is now defined by tickets/open/VISTA-T01.yaml
  and the recovery plan in tickets/open/PIPE-T*.yaml.
  Do not treat MUM-T01..T11 as active tickets — they are a design reference only.
---

# MPIF001 Ticket DAG

## Routine

**MPIF001.m** — Utility Routine of APIs, Master Patient Index VistA  
319 lines · 17 entry points · 5 globals · 9 external routine dependencies

## DAG Visualization

```
MUM-T01 (grammar)
    │
MUM-T02 (parse_mumps → AST)
    ├──────────────────────────────────────────┐
    │                  │           │            │
MUM-T03          MUM-T04      MUM-T05      MUM-T06
(entry_points)  (globals)    (calls)      (queries)
    │                  │           │
    └──────────────────┴───────────┘
               MUM-T07 (summarize)
                    │
               MUM-T08 (emit_stubs)
                    │
               MUM-T09 (write_tests)
                    │
               MUM-T10 (validate_gates)
                    │
               MUM-T11 (write_ATA)
```

## Parallelism

T03, T04, T05, T06 all depend only on T02 and can run concurrently.
In sequential Cline execution, they run T03 → T04 → T05 → T06 in order.

## Tool Map

| Ticket | Primary Tool | Output Artifact |
|--------|-------------|-----------------|
| MUM-T01 | normalize_mumps | output/MPIF001/MPIF001.normalized.m |
| MUM-T02 | parse_mumps | output/MPIF001/MPIF001.ast.json |
| MUM-T03 | list_entry_points | output/MPIF001/MPIF001.entry_points.json |
| MUM-T04 | extract_globals (Phase 3) | output/MPIF001/MPIF001_globals.json |
| MUM-T05 | extract_calls (Phase 3) | output/MPIF001/MPIF001_calls.json |
| MUM-T06 | query_ast (Phase 3) | output/MPIF001/MPIF001_queries.json |
| MUM-T07 | summarize_routine (Phase 3) | output/MPIF001/MPIF001_summary.json |
| MUM-T08 | emit_python_stub | output/MPIF001/stubs.py |
| MUM-T09 | write_file | tests/test_mpif001_stubs.py |
| MUM-T10 | close_ticket (gate check) | GATE-REPORT-MPIF001.md |
| MUM-T11 | journal_writer | logs/luffy-journal.jsonl |

## Iteration to 75 Routines

On completion of the final gate ticket for each routine:
1. Move all routine tickets to tickets/closed/.
2. Update settings.yaml: current_routine to next routine in stack.
3. Generate new ticket DAG for the next routine using this template.
4. Repeat.

Subsequent routine ticket IDs use the routine name as prefix:
MPIF002-T01..T11, MPIFA24-T01..T11, etc.
