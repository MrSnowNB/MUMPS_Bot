# MUMPS_Bot — Changelog

## [rook-reset] — 2026-04-09

### Removed
- `tickets/open/MUM-T01..T11` — stale MPIF001 stack (architecture mismatch: used `blocked/` dir, inline acceptance criteria, wrong output key contracts)
- `tickets/open/HARN-T01..T03` — stale harness bootstrap tickets (referenced non-existent `harness.py`)

### Added
- `tickets/open/ROOK-T01.yaml` — parse ORQQPL1.m → AST JSON (pure JSON, keys: routine, filepath, ast)
- `tickets/open/ROOK-T02.yaml` — list entry points → YAML frontmatter (key: entry_points)
- `tickets/open/ROOK-T03.yaml` — extract globals → YAML frontmatter (key: globals, subkeys: reads/writes)
- `tickets/open/ROOK-T04.yaml` — extract call graph → YAML frontmatter (key: calls)
- `tickets/open/ROOK-T05.yaml` — AST queries (LOCK/GOTO/postconditions) → YAML frontmatter (key: queries)
- `tickets/open/ROOK-T06.yaml` — synthesize summary → YAML frontmatter (key: summary, 5 required subkeys) — depends_on T02/T03/T04/T05
- `tickets/open/ROOK-T07.yaml` — emit Python stubs + write ROOK-ATA.md audit log — depends_on T06
- `tests/rook/test_ROOK_T01.py` through `test_ROOK_T07.py` — pytest gate tests aligned to actual tool output contracts
- `output/.gitkeep` — ensures output/ dir tracked by git before first run

### Changed
- `settings.yaml` — advanced `agent.stage: bud → rook`
- All ROOK tickets use `gate_command: pytest -q tests/rook/test_ROOK_TXX.py` (not inline criteria strings)
- All ROOK tickets use `tickets/failed/` routing (matches `settings.yaml:tickets.failed_dir`)

### DAG
```
ROOK-T01
├── ROOK-T02
├── ROOK-T03
├── ROOK-T04
└── ROOK-T05
         \___all four converge___>
                               ROOK-T06
                                  └── ROOK-T07 → ROOK-ATA.md
```

### Execution
Open `tickets/open/ROOK-T01.yaml` in Cline and say:
> "Execute this ticket. Follow task_steps exactly. Use only allowed_tools. Run gate_command when done."

T01 has no dependencies — it runs immediately. T02/T03/T04/T05 unlock in parallel after T01 closes.
T06 unlocks only when all four fan-out tickets are closed. T07 closes the stack and writes the audit log.
