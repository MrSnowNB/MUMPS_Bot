---
title: Cline Rules Index
version: "3.0"
last_updated: "2026-04-09"
---

# .clinerules — MUMPS_Bot

This directory contains the complete behavioural contract for the Cline executor.
Files are loaded in numeric order. Each file has a unique prefix — no collisions.
All rules are executor-agnostic and model-agnostic.

| File | Scope | Purpose |
|------|-------|---------|
| `00-policy.md` | global | First-principles reasoning, core mandates, scratch enforcement, security |
| `01-file-format.md` | global | Every output file must be `.md` or `.yaml` with frontmatter |
| `02-ticket-schema.md` | global | Ticket YAML schema definition (id, attempts, max_retries, gate_command) |
| `03-lifecycle.md` | orchestrator | Phase gating (Plan→Build→Validate→Review→Release) + ticket state machine |
| `04-failure-handling.md` | global | 5-step failure procedure, retry budget, prohibited actions after halt |
| `05-tools.md` | global | Atomic tool definitions, output filenames, acceptance criteria |
| `06-executor.md` | executor | Ticket execution loop, REASONING/VERIFY events, tool discipline |
| `07-stack-runner.md` | global | Autonomous YOLO loop controller, scratch lifecycle, gate pre-checks |
| `08-toolbox.md` | global | Stage-gated tool registry, MUMPS atomic tools, adding tools |
| `09-audit.md` | global | Immutable JSONL journal, scratchpad schema, mandatory reasoning events |
| `10-log-schema.md` | deprecated | Legacy log schema — superseded by `09-audit.md`. Retained for reference only |

## Skills

| Skill | Purpose |
|-------|---------|
| `skills/ticket-executor/` | How to read, execute, and close a single ticket |
| `skills/spec-writer/` | How to turn a goal into an approved SPEC.md |
| `skills/troubleshoot/` | How to diagnose and document a failure |
| `skills/validate-gates/` | How to run the four validation gates |

## Runtime Config

All executor runtime parameters (endpoint, tools, budget, ticket dirs) live in
`settings.yaml` at the repo root. No model names appear in `.clinerules`.
