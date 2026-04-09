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

1. Confirm the tool is in `allowed_tools`. If not → BLOCKED immediately.
2. Append `TOOL_CALL` event to log.
3. Invoke the tool with the specified input.
4. Append `TOOL_RESULT` event to log (status: ok or error).
5. If status is error:
   - Increment retry counter for this step.
   - If retry_count < 3: apply first-principles diagnosis (see `00-policy.md`) and retry.
   - If retry_count >= 3: move ticket to `tickets/failed/`, append `TICKET_FAILED`, stop.
6. Verify the output file exists and matches expected schema before proceeding.

## Acceptance Gate

After all steps complete:

1. Run every test in `acceptance_criteria` exactly as written.
2. Append one `ACCEPTANCE_CHECK` event per criterion.
3. If ALL pass:
   - Move ticket YAML from `tickets/in_progress/` to `tickets/closed/`.
   - Append `TICKET_CLOSED` event.
4. If ANY fail:
   - Increment retry_count.
   - If retry_count < 3: move back to `tickets/open/`, append `TICKET_FAILED`.
   - If retry_count >= 3: move to `tickets/failed/`, append `TICKET_BLOCKED`.

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
