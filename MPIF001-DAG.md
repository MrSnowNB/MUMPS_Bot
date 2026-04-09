---
title: "MPIF001 Ticket DAG — Guardian Analysis Pipeline"
version: "1.0"
last_updated: "2026-04-09"
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
| MUM-T01 | terminal (pip + build_grammar.py) | tools/mumps/build/mumps.so |
| MUM-T02 | parse_mumps | output/MPIF001/MPIF001_ast.json |
| MUM-T03 | list_entry_points | output/MPIF001/MPIF001_entries.json |
| MUM-T04 | extract_globals | output/MPIF001/MPIF001_globals.json |
| MUM-T05 | extract_calls | output/MPIF001/MPIF001_calls.json |
| MUM-T06 | query_ast (×3) | output/MPIF001/MPIF001_queries.json |
| MUM-T07 | summarize_routine | output/MPIF001/MPIF001_summary.json |
| MUM-T08 | emit_python_stub | output/MPIF001/stubs.py |
| MUM-T09 | write_file | tests/test_mpif001_stubs.py |
| MUM-T10 | terminal (pytest/ruff/mypy) | GATE-REPORT-MPIF001.md |
| MUM-T11 | write_file | output/MPIF001/MPIF001-ATA.md |

## Iteration to 75 Routines

On completion of MUM-T11:
1. Move all MUM-Txx tickets to tickets/closed/.
2. Update settings.yaml: current_routine → <next routine in stack>.
3. Generate new 11-ticket DAG for the next routine.
4. Repeat.

The ticket IDs for subsequent routines use the routine name as prefix:
MPIF002-T01 through MPIF002-T11, MPIFA24-T01 through MPIFA24-T11, etc.
