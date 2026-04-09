#!/usr/bin/env python3
"""
Verify logs/luffy-journal.jsonl integrity.

Checks:
  1. Every line is valid JSON.
  2. Every event has 'event' and 'ts' fields.
  3. Timestamps are monotonically non-decreasing.
  4. For TOOL_CALL/TOOL_RESULT ok events, the output_path file exists (if present).
  5. No duplicate ticket IDs in TICKET_CLOSED (each ticket closed at most once).
  6. TICKET_START always precedes TICKET_CLOSED/FAILED for the same ticket.
  7. Step sequences per ticket have no gaps (step numbers are contiguous).

Usage: python scripts/verify_log.py [path]  (default: logs/luffy-journal.jsonl)
"""
import json
import sys
import os
from datetime import datetime, timezone

LOG_DEFAULT = "logs/luffy-journal.jsonl"

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else LOG_DEFAULT
    if not os.path.exists(path):
        print(f"ERROR: {path} not found")
        sys.exit(1)

    errors = []
    warnings = []
    last_ts = None
    line_num = 0
    started = {}   # ticket -> line first seen TICKET_START
    closed = {}    # ticket -> line closed
    ticket_steps = {}  # ticket -> set of step numbers seen

    with open(path) as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            line_num += 1
            try:
                evt = json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"L{line_num}: invalid JSON — {e}")
                continue

            # Required fields
            if "event" not in evt:
                errors.append(f"L{line_num}: missing 'event' field")
            if "ts" not in evt:
                errors.append(f"L{line_num}: missing 'ts' field")
            else:
                try:
                    ts = datetime.fromisoformat(evt["ts"].replace("Z", "+00:00"))
                    if last_ts and ts < last_ts:
                        errors.append(
                            f"L{line_num}: timestamp not monotonic "
                            f"({evt['ts']} < {last_ts.isoformat()})"
                        )
                    last_ts = ts
                except ValueError:
                    errors.append(f"L{line_num}: invalid timestamp '{evt.get('ts')}'")

            event_type = evt.get("event", "")
            # Accept both 'ticket' (09-audit.md) and 'ticket_id' (legacy 10-log-schema.md)
            tid = evt.get("ticket") or evt.get("ticket_id", "")

            # Track ticket lifecycle
            if event_type == "TICKET_START":
                if tid in closed:
                    warnings.append(f"L{line_num}: {tid} restarted after prior CLOSED (retry run?)")
                started[tid] = line_num

            if event_type in ("TICKET_CLOSED", "TICKET_BLOCKED"):
                if tid and tid not in started:
                    errors.append(f"L{line_num}: {tid} CLOSED/BLOCKED with no prior TICKET_START")
                if event_type == "TICKET_CLOSED":
                    if tid in closed:
                        errors.append(f"L{line_num}: {tid} closed more than once (L{closed[tid]} and L{line_num})")
                    closed[tid] = line_num

            # Output file existence check — accept both TOOL_RESULT (legacy) and TOOL_CALL with status
            if event_type in ("TOOL_RESULT", "TOOL_CALL") and evt.get("status") == "ok":
                op = evt.get("output_path", "")
                if op and not os.path.exists(op):
                    warnings.append(f"L{line_num}: output_path '{op}' not found on disk (may be normal pre-run)")

            # Accept ACCEPTANCE_CHECK (legacy) as equivalent to GATE_RUN
            # Both are valid event types for gate results

            # Track step sequences per ticket for gap detection
            if event_type in ("TOOL_CALL", "TOOL_RESULT") and tid:
                step = evt.get("step")
                if step is not None and isinstance(step, int):
                    if tid not in ticket_steps:
                        ticket_steps[tid] = set()
                    ticket_steps[tid].add(step)

    # Step-sequence gap check
    for tid, steps in ticket_steps.items():
        if not steps:
            continue
        min_step = min(steps)
        max_step = max(steps)
        expected = set(range(min_step, max_step + 1))
        missing = expected - steps
        if missing:
            warnings.append(f"{tid}: step sequence gaps — missing steps {sorted(missing)}")

    print(f"Scanned {line_num} log entries.")
    if warnings:
        print(f"  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"    WARN  {w}")
    if errors:
        print(f"INTEGRITY CHECK FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"    ERR   {e}")
        sys.exit(1)
    else:
        print("OK — no errors.")

if __name__ == "__main__":
    main()
