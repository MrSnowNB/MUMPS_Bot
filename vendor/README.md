---
title: Vendor Dependencies
version: "1.0"
last_updated: "2026-04-09"
---

# Vendor Directory

Contains locally-compiled dependencies not available via pip.

## MUMPS Grammar

`mumps.so` is compiled from [janus-llm/tree-sitter-mumps](https://github.com/janus-llm/tree-sitter-mumps).

Build it:
```bash
bash scripts/build_mumps_grammar.sh
```

This is required because `tree-sitter-languages` has no Python 3.13 wheels,
and `tree-sitter-language-pack` does not include MUMPS.
