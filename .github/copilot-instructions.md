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
