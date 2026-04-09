---
title: Native Toolbox Policy
version: "2.0"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# Native Toolbox Policy

## Tool Registry

All tools are declared in `tools/toolbox.yaml`. The agent may only call tools present
in the registry AND available at its current `agent.stage` (see `00-policy.md`).

Tool call format:

```
TOOL: <tool_name>
PATH: <argument>        ← file path, or primary argument
[CONTENT:
<body>
END]
```

Unknown tools return `ERROR: unknown tool` and do not halt the agent.

## Stage-Gated Access

| Stage   | Tools Available                                                        |
|---------|------------------------------------------------------------------------|
| bud     | read_file, write_file, exec_python                                     |
| branch  | + shell, list_dir                                                      |
| planted | + graphify (knowledge graph over tickets/closed/)                      |
| rooted  | full toolbox, including memory_write, memory_read                      |

The toolbox loader filters by `agent.stage` from `settings.yaml`.
A bud-stage bot calling `graphify` receives:
`ERROR: tool graphify not available at stage bud`.

## Core MUMPS Tools (bud+)

These tools are declared in `tools/toolbox.yaml` and available from stage `bud`:

| Tool              | Purpose                                              |
|-------------------|------------------------------------------------------|
| `parse_mumps`     | Parse a `.m` file → full AST JSON                   |
| `list_entry_points` | List all labels with line ranges from AST          |
| `extract_globals` | Map `^GLOBAL` read/write per entry point            |
| `extract_calls`   | Build cross-routine call graph from AST             |
| `query_ast`       | Run S-expression query against AST                  |
| `summarize_routine` | Synthesize per-entry-point metadata block         |
| `emit_python_stub`| Generate typed Python stub with TODO markers        |

## Adding New Tools

1. Create implementation in `tools/core/` (bud) or `tools/extended/` (branch+)
2. Add entry to `tools/toolbox.yaml` with `name`, `path`, `stage`, `description`, `risk`
3. Update this file's stage table above
4. Human approves before tool becomes active

## Long-Term Tools (Planted+)

### graphify
- Purpose: Build knowledge graphs from unstructured text (ticket logs, results, code)
- Use case: A planted bot running graphify over `tickets/closed/` builds a persistent
  world model of what was tried, what failed, what succeeded
- Risk: high (writes graph files, external dependency)
- Install: `pip install graphify` or local clone into `tools/extended/graphify/`

### memory_write / memory_read (Rooted)
- Purpose: Cross-session persistent state
- Storage: `logs/memory.yaml`
- A rooted bot reads its own history and prunes failed branches autonomously
