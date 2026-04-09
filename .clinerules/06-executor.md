# Executor Behaviour

This file defines how Cline executes a ticket. Follow this protocol exactly.
Do not improvise. Do not skip steps.

## Pre-Flight (before touching any tool)

1. Read the ticket YAML completely.
2. Validate schema against `.clinerules/02-ticket-schema.md`.
3. Check all `depends_on` tickets are in `tickets/closed/`. If not, stop and report which deps are missing.
4. Read all `context_files` listed in the ticket.
5. Move the ticket YAML from `tickets/open/` to `tickets/in_progress/`.
6. Append a `TICKET_START` event to `logs/luffy-journal.jsonl`.

## Execution Loop

For each step in `task_steps` (in order):

1. **Confirm tool authorization.** Verify the tool is in `allowed_tools`. If not → BLOCKED immediately.

2. **First-principles reasoning (mandatory).** Before calling any tool, work through
   the 5-step chain from `00-policy.md` and emit a `REASONING` event to the scratch file:
   ```jsonl
   {"ts":"<ISO8601>","ticket":"<ID>","event":"REASONING","step":<n>,
    "decomposition":"<what is the smallest falsifiable sub-claim?>",
    "ground_truth":"<what is known from evidence, not assumption?>",
    "constraints":"<what cannot change?>",
    "minimal_transform":"<what is the smallest change that satisfies the criteria?>"}
   ```
   This is not optional. If the scratch file does not contain a REASONING event for this
   step when the gate runs, the gate is automatically failed.

3. **Emit TOOL_CALL pending** to `logs/luffy-journal.jsonl` (per `09-audit.md`).

4. **Invoke the tool** with the specified input.

5. **Emit TOOL_CALL ok/error** to `logs/luffy-journal.jsonl` with `elapsed_ms`.

6. **If status is error:**
   - Increment `attempts` in the ticket YAML.
   - If `attempts` < `max_retries`: apply first-principles diagnosis (return to step 2 with new reasoning) and retry.
   - If `attempts` >= `max_retries`: move ticket to `tickets/failed/`, append `TICKET_FAILED`, stop.

7. **Verify and emit VERIFY event.** After the tool call succeeds, verify the output
   against expected results and emit a `VERIFY` event to the scratch file:
   ```jsonl
   {"ts":"<ISO8601>","ticket":"<ID>","event":"VERIFY","step":<n>,
    "expected":"<what the acceptance criteria requires for this step>",
    "actual":"<what the tool actually produced>",
    "pass":<true|false>}
   ```
   If `pass` is false, treat as an error — return to step 2 with corrected reasoning.

8. **Emit STEP_DONE** to the scratch file. Proceed to next step.

## Acceptance Gate

After all steps complete:

0. **Validate scratch file.** Before running any acceptance test, verify:
   - The scratch file `logs/scratch-{ticket_id}.jsonl` exists.
   - It contains a `SCRATCH_INIT` event.
   - It contains at least one `REASONING` event and one `VERIFY` event for every
     task_step that was executed.
   - All `VERIFY` events have `"pass": true`.
   If any of these checks fail, the gate is automatically FAILED — do not run the
   acceptance test. Append `GATE_RUN` with `status: fail` and
   `reason: "scratch validation failed: <specific missing element>"`.

1. Run every test in `acceptance_criteria` exactly as written.
2. Append one `ACCEPTANCE_CHECK` event per criterion.
3. If ALL pass:
   - Move ticket YAML from `tickets/in_progress/` to `tickets/closed/`.
   - Append `TICKET_CLOSED` event.
4. If ANY fail:
   - Increment `attempts` in the ticket YAML.
   - If `attempts` < `max_retries`: move back to `tickets/open/`, append `TICKET_RETRY`.
   - If `attempts` >= `max_retries`: move to `tickets/failed/`, append `TICKET_BLOCKED`.

## Post-Ticket

1. Report to the operator: ticket ID, status, artifacts produced, any warnings.
2. List the next OPEN tickets whose `depends_on` are now all CLOSED.
3. Ask: "Proceed with [next ticket ID]?"

## What Cline Must Never Do

- Never modify source `.m` files.
- Never delete log entries.
- Never call a tool not in `allowed_tools`.
- Never mark a ticket CLOSED without running all acceptance criteria.
- Never assume a prior run's output is valid — re-verify on every retry.
