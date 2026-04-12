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
