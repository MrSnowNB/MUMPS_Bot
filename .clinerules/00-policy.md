# Guardian Harness — Execution Policy

## First Principles Reasoning Protocol

Before taking any action on a ticket, work through these five steps in order.
Do not skip steps. Document each step as a comment in the log entry.

1. **Decompose** — Break the ticket's goal into the smallest falsifiable sub-claims.
   Ask: "What is the minimum unit of work that can be independently verified?"

2. **Establish Ground Truth** — Identify what is *known* from evidence, not assumption.
   Only AST output, file contents, and tool results count as evidence.
   Pattern-matched guesses are not ground truth.

3. **Identify Constraints** — List what cannot change:
   - The MUMPS source is read-only.
   - Output schema is fixed by `output/README.md`.
   - Tool calls are limited to `allowed_tools` in the ticket.
   - Acceptance criteria are pass/fail gates, not guidelines.

4. **Find the Minimal Transformation** — Given ground truth and constraints,
   what is the smallest change that satisfies the acceptance criteria?
   Prefer tool calls over prose reasoning. Prefer one tool call over two.

5. **Verify Against Ground Truth** — After producing output, re-run the
   acceptance test from the ticket. If it fails, return to step 1.
   Do not proceed to the next ticket until the current one is CLOSED.

### Scratch Enforcement

The five-step chain above is not advisory — it is a structural requirement.
Every step must produce a corresponding event in the scratch file before the
tool call it governs. If a scratch file is missing, empty, or lacks REASONING
events for any executed task_step, the gate MUST be failed regardless of
whether the acceptance test itself passes.

The scratch file is the proof that first-principles reasoning occurred.
Without it, a passing gate is meaningless — the result is unauditable.

## Hard Rules

- Never modify files in `tickets/open/` during execution — those are immutable specs.
- Write ALL output to `output/` — never to the source tree.
- Append to `logs/luffy-journal.jsonl` after EVERY tool call (success or failure).
- If a tool call fails 2 attempts with the same input, set ticket status BLOCKED and stop.
- Never invoke a tool not listed in the ticket's `allowed_tools`.
- Never reference a model name, API endpoint, or hardware spec in reasoning or logs.
  The harness is model-agnostic. Intelligence comes from the protocol, not the backend.
- Write a REASONING event to the scratch file BEFORE every tool call. The event must contain
  the decomposition, ground truth, constraints, and minimal transformation from the 5-step chain.
  Skipping the scratch write is a protocol violation equivalent to skipping the tool call itself.
- Write a VERIFY event to the scratch file AFTER every task_step completes. The event must contain
  expected outcome, actual outcome, and pass/fail status. This is the evidence that step 5 was executed.

## Ticket Status Transitions

```
OPEN → IN_PROGRESS  (when Cline picks up the ticket)
IN_PROGRESS → CLOSED   (all acceptance criteria pass)
IN_PROGRESS → FAILED   (any criterion fails; attempts < max_retries)
FAILED → OPEN          (ready for retry)
FAILED → BLOCKED       (attempts >= max_retries; human/escalation required)
```

Move the YAML file to the matching directory to record the transition.
