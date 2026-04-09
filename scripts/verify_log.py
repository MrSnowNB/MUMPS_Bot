#!/usr/bin/env python3
"""Verify luffy-journal.jsonl integrity."""
import json
import sys
import os
from datetime import datetime

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/luffy-journal.jsonl"
    if not os.path.exists(path):
        print(f"ERROR: {path} not found")
        sys.exit(1)

    errors = []
    last_ts = None
    line_num = 0

    with open(path) as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            line_num += 1
            try:
                evt = json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: invalid JSON — {e}")
                continue

            # Required fields
            if "event" not in evt:
                errors.append(f"Line {line_num}: missing 'event' field")
            if "ts" not in evt:
                errors.append(f"Line {line_num}: missing 'ts' field")
            else:
                try:
                    ts = datetime.fromisoformat(evt["ts"].replace("Z", "+00:00"))
                    if last_ts and ts < last_ts:
                        errors.append(f"Line {line_num}: timestamp not monotonic ({evt['ts']} < {last_ts.isoformat()})")
                    last_ts = ts
                except ValueError:
                    errors.append(f"Line {line_num}: invalid timestamp format")

            # Check referenced output files exist
            if evt.get("event") == "TOOL_RESULT" and evt.get("status") == "ok":
                op = evt.get("output_path", "")
                if op and not os.path.exists(op):
                    errors.append(f"Line {line_num}: output_path '{op}' does not exist")

    if errors:
        print(f"INTEGRITY CHECK FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"OK — {line_num} log entries verified, no errors.")

if __name__ == "__main__":
    main()
