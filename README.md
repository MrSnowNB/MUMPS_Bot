# MUMPS_Bot — Guardian Harness

A model-agnostic Cline execution harness for iterative MUMPS→Python translation
using tree-sitter-mumps as the analysis backbone.

## Architecture

```
SOTA Model (cloud, one-time)        Local Executor (Ollama + Gemma)
  ↓ decomposes goal                    ↓ reads tickets
  ↓ writes ticket DAG               tickets/open/*.yaml
  ↓ points at Fractal_Claws            ↓ runs atomic tools
                                     output/*.json / *.py
                                        ↓ appends events
                                     logs/luffy-journal.jsonl
```

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/MrSnowNB/MUMPS_Bot.git
cd MUMPS_Bot

# 2. Install Python deps
pip install -r requirements.txt

# 3. Check which tickets are ready
python scripts/next_ticket.py

# 4. Open the first ready ticket in Cline and say:
#    "Execute this ticket. Follow task_steps exactly.
#     Use only allowed_tools. Log every action to logs/luffy-journal.jsonl."

# 5. Verify log integrity at any time
python scripts/verify_log.py logs/luffy-journal.jsonl

# 6. Reset all tickets to OPEN
python scripts/reset_tickets.py
```

## Ticket Families

| Family | Prefix | Purpose |
|--------|--------|---------|
| MUMPS Parse | `MUM-T*` | Parse MPIF001.m → AST → stubs → ATA |
| Environment | `BUILD-T*` | Docker + Ollama + Gemma setup |
| Executor Loop | `ROOK-T*` | Python runner + ticket state machine |
| Harness Wiring | `HARN-T*` | Cline rules + audit log + verification |

## Key Files

| File | Purpose |
|------|---------|
| `.clinerules/00-policy.md` | First-principles execution protocol |
| `.clinerules/01-tools.md` | 7 atomic tree-sitter tool definitions |
| `.clinerules/02-ticket-schema.md` | YAML schema reference |
| `.clinerules/03-log-schema.md` | Audit log event schemas |
| `.clinerules/04-executor.md` | Cline step-by-step execution protocol |
| `MPIF001-DAG.md` | 11-ticket dependency graph for MPIF001.m |
| `tickets/open/` | All OPEN tickets (ready or waiting on deps) |
| `logs/luffy-journal.jsonl` | Append-only audit trail |
| `output/` | All artifacts from ticket execution |

## Related Repos

- [WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M) — MUMPS source
- [janus-llm/tree-sitter-mumps](https://github.com/janus-llm/tree-sitter-mumps) — Parser
- [MrSnowNB/Fractal_Claws](https://github.com/MrSnowNB/Fractal_Claws) — Cline runes origin
