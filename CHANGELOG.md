# MUMPS_Bot — Changelog

## [build-reset] — 2026-04-09 (second reset)

### Root Cause
All 7 `tools/mumps/*.py` used `Language(str(grammar_path), 'mumps')` pointing to
`tools/mumps/build/mumps.so` — a compiled binary that was never built or committed.
Every tool would crash with `FileNotFoundError` before any MUMPS parsing occurred.
Additionally, `summarize_routine.py` hardcoded output paths incompatible with how
tickets actually write files. `runner.py` had no `model` field in settings.yaml.
No `requirements.txt` existed.

### Changes

#### Fixed — tools/mumps/
- All 7 tools rewritten to use `tree_sitter_languages.get_language('mumps')` and
  `tree_sitter_languages.get_parser('mumps')` — pre-built binary, no compile step
- `summarize_routine.py` — changed to accept explicit `--entries`, `--globals`,
  `--calls` file paths instead of hardcoded `output/<stem>/` paths
- `emit_python_stub.py` — reads `routine_name` key (was `routine`), writes to
  `output/<stem>-stub.py` (flat output dir, no subdirectory)
- All tools write flat to `output/<ROUTINE>-<type>.json` (no subdirectory)
- All tools have CLI `--help`-compatible argparse or sys.argv usage docs

#### Added
- `requirements.txt` — pinned: tree-sitter>=0.22,<0.24; tree-sitter-languages>=1.10.2;
  pyyaml>=6.0.2; pytest>=8.0; ruff>=0.4
- `tickets/open/BUILD-T01..T07` — ticketed tool verification stack
- `tests/build/test_BUILD_T01..T07.py` — pytest gate tests for each BUILD ticket

#### Changed
- `settings.yaml` — added `executor.model: gemma4` field (was missing, runner fell
  back to hardcoded string 'gemma4' inside runner.py payload)
- `tickets/open/ROOK-T01..T07` — cleared (tools not verified yet; ROOK stack will
  be re-added after BUILD stack closes)
- `logs/journal.md` — reset to clean header
- `ISSUE.md` — reset to clean header

### New Execution Order
```
BUILD-T01  verify tree-sitter-languages grammar loads
    └── BUILD-T02  parse_mumps.py smoke test on sample.m
           ├── BUILD-T03  list_entry_points.py
           └── BUILD-T04  extract_globals.py + extract_calls.py
           └── BUILD-T05  query_ast.py
                    └── BUILD-T06  summarize_routine.py + emit_python_stub.py
                              └── BUILD-T07  runner.py dry-run
```
Once BUILD-T07 closes: ROOK stack re-added pointing at ORQQPL1.m with
confirmed-working tools and correct output paths.
