---
title: Cline Rules Index
version: "2.0"
last_updated: "2026-04-09"
---

# .clinerules — MUMPS_Bot

This directory contains the complete behavioural contract for the Cline executor.
Files are loaded in numeric order. All rules are executor-agnostic and model-agnostic.

| File | Scope | Purpose |
|------|-------|---------|
| `00-policy.md` | global | First-principles reasoning, core mandates, lifecycle, gates, security |
| `01-file-format.md` | global | Every output file must be `.md` or `.yaml` with frontmatter |
| `02-lifecycle.md` | orchestrator | Phase gating (Plan→Build→Validate→Review→Release) + ticket state machine |
| `03-failure-handling.md` | global | 5-step failure procedure, retry budget, prohibited actions after halt |
| `04-executor.md` | executor | Ticket execution loop, tool discipline, context management |
| `05-toolbox.md` | global | Stage-gated tool registry, MUMPS atomic tools, adding tools |

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
