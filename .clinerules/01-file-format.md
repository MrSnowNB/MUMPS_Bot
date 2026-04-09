---
title: File Format Standards
version: "1.1"
scope: global
applies_to: all_agents
last_updated: "2026-04-09"
---

# File Format Standards

## Rule

Every file created or modified by an agent must be one of:

- **Markdown with YAML frontmatter** — `.md` files beginning with a `---` block
- **Pure YAML** — `.yaml` or `.yml` files with no free-form prose

No agent may produce `.txt`, `.toml`, `.ini`, `.csv`, or binary files unless
the human operator explicitly overrides this rule in the task spec.

## Tool Output Exemption

**JSON files (`.json`) are permitted when produced by tool scripts in `tools/`**
or when a ticket's `result_path` or `gate_command` explicitly expects JSON output.
This exemption exists because tree-sitter tools emit AST data as JSON, and the
acceptance gates validate JSON schema. The exemption applies only to files written
under `output/`. All human-readable documentation and ticket artifacts remain
Markdown with YAML frontmatter.

## Python File Exemption

**Python files (`.py`) are permitted when produced by `emit_python_stub` or
when a ticket's `result_path` ends in `.py` or `.py.md`.** Stub files that
contain Python inside a Markdown code fence use the `.py.md` extension.

## YAML Frontmatter Minimum Fields

Every `.md` file must include at minimum:

```yaml
---
title: <descriptive title>
version: "<semver or date string>"
last_updated: "<YYYY-MM-DD>"
---
```

## Validation

Before writing any file, the agent must verify:
1. The extension is `.md`, `.yaml`, `.yml`, `.json` (tool output only), or `.py` (stub only)
2. For `.md` files: frontmatter block opens and closes with `---`
3. Required fields are present and non-empty

Violation of this rule constitutes a policy failure → trigger full failure handling procedure.
