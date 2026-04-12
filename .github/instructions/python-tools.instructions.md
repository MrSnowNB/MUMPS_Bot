---
applyTo: "tools/mumps/*.py"
---

# MUMPS tool instructions

- These scripts are deterministic analysis or emission tools, not AI agents.
- Do not introduce randomness, heuristics, or model-based reasoning.
- Preserve the deterministic behavior of MUMPS constructs (e.g., $PIECE, $GET, $LENGTH).
- Output must match the schema defined in `output/README.md`.
- Every tool call must emit REASONING and VERIFY events to the scratch file.
- Never write to source files in `routines/` - output only to `output/`.
- Keep tool outputs reproducible and traceable to source lines.
