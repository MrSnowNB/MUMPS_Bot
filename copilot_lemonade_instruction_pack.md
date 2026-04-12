# GitHub Copilot + Lemonade instruction pack for MUMPS_Bot

This document converts the repository's `.clinerules` policy set into a Copilot-friendly format that is compact enough for Lemonade-backed local inference while preserving the project's core execution discipline.[cite:9]

## Why this works

GitHub Copilot in VS Code supports repository-level custom instructions, and those instructions can be used to steer Copilot even when the request is routed through a Copilot-compatible backend.[cite:web:11][cite:web:10] MUMPS_Bot already defines its operating model in `.clinerules`, including policy, ticket schema, lifecycle, tools, executor behavior, and audit requirements.[cite:9]

## Source rule emphasis

The generated instructions below were distilled from the repository policy files most relevant to Copilot behavior: `00-policy.md`, `02-ticket-schema.md`, `03-lifecycle.md`, `05-tools.md`, `06-executor.md`, and `09-audit.md`.[cite:9] Those files define the deterministic-router model, the YAML ticket contract, lifecycle constraints, active versus forbidden tools, and the append-only audit expectations that should survive the move from Cline-style rules to Copilot-style instructions.[cite:6][cite:9]

## Recommended file map

Create these files in the repository:[cite:web:11]

- `.github/copilot-instructions.md`
- `.github/instructions/tickets.instructions.md`
- `.github/instructions/python-tools.instructions.md`

## .github/copilot-instructions.md

```md
# Repository instructions for GitHub Copilot (Lemonade-safe)

You are working in the MUMPS_Bot repository.

Follow these rules strictly:

## Mission
- Act as an execution router and disciplined repository assistant.
- Prefer deterministic edits, small diffs, and explicit validation.
- Do not invent architecture, tools, workflow steps, or data.

## Core constraints
- Do not interpret MUMPS semantics or rewrite business logic creatively.
- Do not use the model as the translator when a deterministic script or ticketed tool is responsible for the work.
- Do not bypass ticket dependencies, lifecycle rules, or audit requirements.
- Do not overwrite or truncate append-only journal data.
- Do not introduce new file formats when an existing project format already exists.

## Ticket handling
- Tickets are YAML documents and must stay schema-compliant.
- Keep `depends_on` in inline list form, for example: `depends_on: [BOOT-T01, PIPE-T02]` or `depends_on: []`.
- Preserve ticket IDs, titles, tool names, paths, gates, and dependency semantics unless the task explicitly requires changing them.
- Respect lifecycle intent: `open -> in_progress -> closed` or `failed`.

## Tool discipline
- Only reference tools that physically exist in the repository and are active in current policy.
- Treat these as allowed executor tools unless the user explicitly changes policy: `normalize_mumps`, `parse_mumps`, `list_entry_points`, `build_ir`, `emit_python_stub`, `journal_writer`, `run_tool`, `next_ticket`, `close_ticket`, `check_skeleton`.
- Treat these as forbidden in the current phase unless policy is explicitly changed: `browser`, `web_fetch`, `computer_use`, `code_interpreter`, `extract_globals`, `extract_calls`, `query_ast`, `summarize_routine`.
- Never suggest phantom tools or capabilities that are not implemented in the repo.

## Audit and logging
- Preserve the audit-first mindset for any workflow suggestions.
- Before a tool action, require a REASONING record; after validation, require a VERIFY record.
- Assume the project journal is append-only and must never be truncated or replaced.
- When proposing automation, include journal and scratch-log compliance.

## Editing style
- Prefer minimal patches over broad rewrites.
- Keep naming, folder layout, and repo conventions consistent.
- When changing tickets, prioritize dependency correctness, schema consistency, and diff clarity.
- When changing tools, preserve deterministic behavior, structured JSON outputs, and reproducibility.

## Response style
- Be direct and operational.
- State assumptions when uncertain.
- If a request would violate policy, say so and offer the nearest compliant alternative.
```

## .github/instructions/tickets.instructions.md

```md
---
applyTo: "tickets/**/*.yaml"
---

# Ticket file instructions

- Output valid YAML only.
- Preserve the project ticket schema.
- Keep `depends_on` as an inline list.
- Do not remove dependencies unless explicitly asked.
- Do not add tools that are forbidden in current policy.
- Keep paths relative to the repository.
- Preserve gates as deterministic checks, not natural-language wishes.
- Prefer small, auditable edits.
```

## .github/instructions/python-tools.instructions.md

```md
---
applyTo: "tools/mumps/*.py"
---

# MUMPS tool instructions

- These scripts are deterministic analysis or emission tools, not AI agents.
- Do not add model inference, web access, or hidden external dependencies.
- Preserve structured machine-readable output.
- Favor standard-library or already-declared dependencies.
- Maintain reproducibility: same input should produce the same output.
- Keep audit compatibility intact when reading, transforming, or writing artifacts.
- Prefer focused functions and minimal side effects.
```

## Notes

This pack is intentionally minimal so it fits local-model context budgets more comfortably while still carrying over the most important constraints from the repo's current execution policy.[cite:web:22][cite:6] The highest-value rules to keep are dependency discipline, allowed-versus-forbidden tool awareness, deterministic edits, and audit-log preservation.[cite:6][cite:7][cite:9]
