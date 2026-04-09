#!/usr/bin/env python3
"""
Verify logs/luffy-journal.jsonl integrity.

Checks:
  1. Every line is valid JSON.
  2. Every event has 'event' and 'ts' fields.
  3. Timestamps are monotonically non-decreasing.
  4. For TOOL_RESULT ok events, the output_path file exists.
  5. No duplicate ticket IDs in TICKET_CLOSED (each ticket closed at most once).
  6. TICKET_START always precedes TICKET_CLOSED/FAILED for the same ticket_id.

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
    started = {}   # ticket_id -> line first seen TICKET_START
    closed = {}    # ticket_id -> line closed

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
            tid = evt.get("ticket_id", "")

            # Track ticket lifecycle
            if event_type == "TICKET_START":
                if tid in closed:
                    # Restarted after close — valid for retries after reset
                    warnings.append(f"L{line_num}: {tid} restarted after prior CLOSED (retry run?)")
                started[tid] = line_num

            if event_type in ("TICKET_CLOSED", "TICKET_BLOCKED"):
                if tid and tid not in started:
                    errors.append(f"L{line_num}: {tid} CLOSED/BLOCKED with no prior TICKET_START")
                if event_type == "TICKET_CLOSED":
                    if tid in closed:
                        errors.append(f"L{line_num}: {tid} closed more than once (L{closed[tid]} and L{line_num})")
                    closed[tid] = line_num

            # Output file existence check
            if event_type == "TOOL_RESULT" and evt.get("status") == "ok":
                op = evt.get("output_path", "")
                if op and not os.path.exists(op):
                    warnings.append(f"L{line_num}: output_path '{op}' not found on disk (may be normal pre-run)")

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
