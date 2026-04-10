# deprecated/

This directory holds files that have been superseded or invalidated by the
recovery plan implemented on 2026-04-09.

Do **not** import, execute, or reference any file in this directory.
Files are preserved here for historical reference only.

## Contents

| File | Original Location | Reason Deprecated |
|------|------------------|-------------------|
| `sample.m` | `sample.m` (root) | Uses globals (`^MyData`); not a valid pipeline fixture. Superseded by `routines/hello_message.m` + `SMOKE-T01.yaml`. |
| `mumps_cmds.txt` | `mumps_cmds.txt` (root) | Raw abbreviated snippets with no provenance. Superseded by `tools/mumps/normalize_mumps.py` `COMMAND_MAP`. |
| `agent_runner.py.archived` | `agent/runner.py.archived` | Monolithic pre-recovery runner. Superseded by `scripts/run_tool.py`. |
| `agent_scheduler.py.archived` | `agent/scheduler.py` | Used `---` front-matter YAML format incompatible with recovery plan ticket format. Superseded by `scripts/next_ticket.py`. |
