# MUMPS_Bot

**A deterministic MUMPS-to-Python translation pipeline with a complete audit trail.**

MUMPS_Bot translates VistA MUMPS routines into Python — not by having an AI "rewrite" the code, but by running a fixed chain of tree-sitter analysis tools in dependency order. The output is a 1:1 structural translation where every Python line traces back to a specific MUMPS line, with cryptographic hashes at each stage.

The AI model is a **smart router**. It reads the next ticket, calls the right tool, checks the gate, logs the result, and moves on. It never interprets MUMPS semantics. It never decides what a global variable means. It never rewrites anything.

---

## Why This Architecture

VistA processes medical records for millions of veterans. The MUMPS routines that power it touch patient PII/PHI protected under HIPAA, and operational data subject to federal audit requirements. Any transformation of this code must be:

- **Deterministic** — same input produces same output, every time
- **Auditable** — every step logged with inputs, outputs, and timestamps
- **Traceable** — any line of output Python maps back to its source MUMPS line
- **Reproducible** — delete the outputs, re-run the pipeline, get identical results

An AI model that "understands" MUMPS and rewrites it in Python creates an unauditable black box. You cannot prove the output is correct because the reasoning was opaque, non-deterministic, and unreproducible.

This project eliminates that problem by separating **scheduling** from **translation**. The translation logic lives in deterministic Python scripts. The AI model is the scheduler.

---

## The Smart Router

The executor model is deliberately the **smallest model available that has reliable tool calling**. It does not need to understand MUMPS. It does not need to write code. It needs to:

1. Read a YAML ticket
2. Identify which tool to call and with what arguments
3. Execute the tool via shell
4. Check whether the output satisfies the acceptance gate
5. Log everything to the journal
6. Move the ticket to `closed/` or `failed/`
7. Pick up the next ticket whose dependencies are satisfied

That is the entire cognitive load. A model that is bored by its workload is a model that does not hallucinate. Overpowered models improvise. Underpowered models fail to parse the ticket. The right model is the smallest one that can reliably do structured tool dispatch.

### What the router never does

- Names or references the model executing it
- Interprets MUMPS code semantics
- Makes translation decisions
- Skips logging to the journal
- Executes a ticket with unclosed dependencies
- Writes output in formats not defined in the file-format policy
- Downloads code or data from the internet
- Overwrites an existing journal entry

### What the router always does

- Writes a REASONING event before calling any tool
- Writes a VERIFY event after checking the gate
- Logs to both the immutable journal and the per-ticket scratch file
- Fails the gate if scratch validation is incomplete

---

## The Tool Chain

Seven atomic tools form the translation pipeline. Each is a standalone Python script that takes a file path and produces structured JSON. No tool depends on the model. No tool uses AI inference. Every tool is a pure function.

| # | Tool | Input | Output | Purpose |
|---|------|-------|--------|---------|
| 1 | `parse_mumps` | `.m` file | AST JSON | Parse source into tree-sitter AST |
| 2 | `list_entry_points` | `.m` file | Entry point array | Extract all labels with line ranges |
| 3 | `extract_globals` | `.m` file | Global read/write map | Map every `^GLOBAL` access by entry point |
| 4 | `extract_calls` | `.m` file | Call graph array | Build cross-routine call graph |
| 5 | `query_ast` | `.m` file | Complexity markers | Find LOCKs, GOTOs, postconditionals |
| 6 | `summarize_routine` | JSON files | Routine summary | Synthesize per-entry-point metadata |
| 7 | `emit_python_stub` | Summary JSON | `.py` stub | Generate typed Python with line-mapped TODOs |

Tools 1–5 use [tree-sitter-mumps](https://github.com/janus-llm/tree-sitter-mumps) (Apache-2.0, MITRE public release Case #23-4084). Tools 6–7 are stdlib-only synthesis scripts.

The tool chain is a **compiler middle-end**: source → AST → analysis passes → IR → code generation. The model is `make`. The tools are the compiler.

---

## The Ticket System

Work is organized as YAML tickets in a directed acyclic graph (DAG). Each ticket specifies:

```yaml
ticket_id: ROOK-T01
title: Parse ORQQPL1.m into AST
depends_on: []
tool: parse_mumps
tool_args: ["routines/ORQQPL1.m"]
result_path: output/ORQQPL1-ast.json
gate: "ast.type == 'program'"
context_files:
  - routines/ORQQPL1.m
  - .clinerules/05-tools.md
```

The executor picks the next ticket whose `depends_on` list is fully closed, runs it, and checks the gate. If the gate fails three times, the ticket moves to `failed/` and execution halts on that branch.

### Ticket lifecycle

```
tickets/open/       → picked up by router
tickets/in_progress/→ tool is running
tickets/closed/     → gate passed, logged
tickets/failed/     → gate failed 3x, needs human review
```

### The 75-routine strategy

The VistA-M sample set contains 75 representative routines. This project builds the complete ticket DAG for **one routine first**, proving the tool chain end-to-end. Once validated:

- The ticket DAG becomes a **template** — swap the routine name, re-run
- The JSON output schemas become **frozen contracts** — any routine must conform or throw a structured error
- The atomic tools become composable into **higher-order tools** (e.g., `translate_routine` = all 7 steps in sequence)

Iterate one routine at a time. Never batch. Every routine gets its own ticket stack, its own scratch files, its own journal entries.

---

## The Audit Trail

Every tool invocation produces entries in two locations:

1. **`logs/luffy-journal.jsonl`** — the immutable, append-only project journal. Every action that reads, transforms, or writes representations of MUMPS source code is logged here before and after execution. This journal is never truncated.

2. **`logs/scratch-{ticket_id}.jsonl`** — the per-ticket reasoning trail. Contains REASONING events (why the router chose this action) and VERIFY events (what the gate check found). The scratch file is validated before a ticket can close.

### Why dual-write

The journal is the **audit artifact**. If a regulator asks how a specific Python stub was produced, the journal provides a complete chain from source parse to code emission with timestamps and content hashes at every step.

The scratch file is the **execution proof**. It demonstrates that the router followed protocol — reasoned before acting, verified after acting — for every single step. A ticket that passes its acceptance gate but has an incomplete scratch file still fails.

### Medical data notice

This system processes MUMPS source code from clinical information systems. All actions that read, transform, or write representations of that code are logged. The journal is append-only and must never be truncated. See `.clinerules/09-audit.md` for the full audit mandate.

---

## The 1:1 Translation Constraint

The output must preserve MUMPS semantics exactly. This is not refactoring. This is not modernization. This is structural translation.

- `S X=$$EN^ROUTINE(Y)` → `X = ROUTINE.EN(Y)` — not a "better" API
- `I X D THING` → `if X: THING()` — exact branch logic preserved
- `^DPT(DFN,0)` → `DPT[DFN][0]` or typed accessor — same access pattern
- `LOCK +^DPT(DFN)` → threading primitive with same granularity
- Every output line carries `# MUMPS line N` for traceability

The stub file is not the final product. It is a **scaffold** with TODO markers at every translation point that requires human verification. The pipeline produces the scaffold deterministically. Humans verify the semantics. The journal proves the pipeline ran correctly.

---

## Project Structure

```
MUMPS_Bot/
├── .clinerules/          # Execution policy (file format, tools, lifecycle, audit)
├── docs/                 # Architecture diagrams and guides
├── logs/                 # Journal + scratch files (gitignored except .gitkeep)
├── output/               # Tool outputs (gitignored except .gitkeep)
├── routines/             # MUMPS .m source files (read-only inputs)
├── scripts/              # Utility scripts (fetch, reset, next-ticket)
├── tickets/              # Ticket DAGs (open/in_progress/closed/failed)
│   └── open/             # Ready for execution
├── tools/
│   └── mumps/            # The 7 atomic analysis tools
├── settings.yaml         # Runtime configuration (model-agnostic)
├── START.md              # Rook session context (entrypoint for executor)
└── README.md             # This file
```

---

## Getting Started

```bash
# 1. Clone
git clone https://github.com/MrSnowNB/MUMPS_Bot.git
cd MUMPS_Bot

# 2. Install dependencies
pip install tree-sitter-languages>=1.10.2

# 3. Fetch a routine from VistA-M
bash scripts/fetch_routine.sh ORQQPL1

# 4. Check the ticket queue
python scripts/next_ticket.py

# 5. Point your executor at START.md and say:
#    "Execute the open ticket stack."
```

The executor model, runtime container, and inference endpoint are not specified here. They are deployment decisions. The harness accepts any model that can read YAML, call shell commands, and write JSON. Choose the smallest one that does this reliably.

---

## Related Repositories

- [WorldVistA/VistA-M](https://github.com/WorldVistA/VistA-M) — OSEHRA VistA M components (source routines)
- [janus-llm/tree-sitter-mumps](https://github.com/janus-llm/tree-sitter-mumps) — MUMPS grammar for tree-sitter (Apache-2.0, MITRE)
- [MrSnowNB/Fractal_Claws](https://github.com/MrSnowNB/Fractal_Claws) — Execution harness patterns adapted for this project

---

## License

This project processes open-source VistA-M routines. The tree-sitter-mumps grammar is Apache-2.0 (MITRE public release Case #23-4084). The harness, tools, and ticket system in this repository are provided as-is for proof-of-concept purposes.
