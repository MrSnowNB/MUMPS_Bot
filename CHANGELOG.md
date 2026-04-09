# Changelog

All notable changes to MUMPS_Bot are documented here.

## [Unreleased]

## [0.3.0] — 2026-04-09

### Reset & Verification
- All tickets reset to OPEN state
- Logs cleared with fresh HARNESS_RESET event
- Full `.clinerules/` suite verified and pushed:
  - `00-policy.md` — First-principles 5-step protocol (model-agnostic)
  - `01-tools.md` — 7 atomic tree-sitter tool definitions with full schemas
  - `02-ticket-schema.md` — Canonical YAML ticket schema
  - `03-log-schema.md` — Full audit log event schemas
  - `04-executor.md` — Cline execution protocol (no model/hardware refs)
- `scripts/verify_log.py` — Log integrity checker
- `scripts/reset_tickets.py` — Programmatic ticket reset
- `scripts/next_ticket.py` — DAG-aware next-ticket advisor
- `output/README.md` — Artifact naming convention + integrity contract
- `tickets/README.md` — State machine docs + reset procedure
- `logs/README.md` — Log schema reference
- `logs/luffy-journal.jsonl` — Reset to single HARNESS_RESET entry

## [0.2.0] — 2026-04-09

### Added
- 28-file Guardian Harness initial commit
- 11-ticket MUM-T* DAG for MPIF001.m translation
- 7 BUILD-T* environment setup tickets (Docker + Ollama)
- 7 ROOK-T* executor loop tickets
- 3 HARN-T* harness wiring tickets
- MPIF001-DAG.md dependency graph
- toolbox.yaml tool registry
- settings.yaml execution semantics

## [0.1.0] — 2026-04-08

### Added
- Initial repo scaffold from Fractal_Claws rune adaptation
- sample.m MUMPS test fixture
- requirements.txt
- Basic .clinerules structure
