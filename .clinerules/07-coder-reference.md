---
title: Coder Reference (Non-Active — Reference Only)
version: "1.1"
scope: reference
applies_to: human_operator
last_updated: "2026-04-09"
---

# Coder Reference Rules

> **NOTE**: This file is numbered 07 and is a reference document only.
> It is NOT active policy. The active executor rules are in `04-executor.md`.
> Renamed from `04-coder.md` to resolve numeric prefix collision (Bug B2).
> Model-specific thinking budget guidance is preserved here for reference.

## Thinking Budget (Reference)

- **Plan phase**: Full thinking blocks enabled — required for task decomposition and spec drafting
- **Build phase**: Suppress thinking for file writes and terminal commands
- **Validate phase**: Enable thinking only when interpreting ambiguous gate output
- **Review and Release**: No thinking required

Rationale: thinking blocks consume context at ~4-8x the rate of direct output.
On a 128K context window, unconstrained thinking in Build phase exhausts the budget
before the task completes.

## Tool Call Discipline

- Issue one tool call at a time — wait for the result before issuing the next
- Never chain tool calls speculatively
- If a tool call result is ambiguous, evaluate before proceeding

## Context Management

- At 60% context utilization: write a checkpoint summary to `CHECKPOINT.md` and continue
- At 80% context utilization: halt, summarize state to `CHECKPOINT.md`, alert human
- Never attempt to continue a task that cannot be completed within the remaining context budget
