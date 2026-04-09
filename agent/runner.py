#!/usr/bin/env python3
"""
runner.py — single-bot ticket executor for MUMPS_Bot harness.

Model-agnostic. All runtime config from settings.yaml.
Usage:
    python agent/runner.py               # run until stack exhausted or halt
    python agent/runner.py --once        # run exactly one ticket then exit
    python agent/runner.py --ticket MUM-T02  # run a specific ticket by ID
    python agent/runner.py --dry-run     # print next ticket, do not execute
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
settings = yaml.safe_load((ROOT / "settings.yaml").read_text())

TICKETS_OPEN = ROOT / settings["tickets"]["open_dir"]
TICKETS_IP   = ROOT / settings["tickets"]["in_progress_dir"]
TICKETS_CLOSED = ROOT / settings["tickets"]["closed_dir"]
TICKETS_FAILED = ROOT / settings["tickets"]["failed_dir"]
LOGS_DIR     = ROOT / settings["logging"]["dir"]
LOGS_DIR.mkdir(exist_ok=True)

JOURNAL = ROOT / settings["logging"].get("journal", "logs/journal.md")
SESSION_LOG = LOGS_DIR / f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

MAX_RETRIES = settings["tickets"]["max_retries_default"]


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log_event(ticket_id: str, step: int, tool: str, path: str,
              result: str, tokens: int = 0) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "step": step,
        "tool": tool,
        "path": path,
        "result": result,
        "tokens_used": tokens,
    }
    with SESSION_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{ticket_id}] step={step} tool={tool} -> {result}")


def journal_entry(ticket_id: str, status: str, note: str = "") -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"| {ts} | {ticket_id} | {status} | {note} |\n"
    if not JOURNAL.exists():
        JOURNAL.write_text(
            "---\ntitle: Execution Journal\nversion: \"1.0\"\nlast_updated: \"\"\n---\n\n"
            "# Execution Journal\n\n"
            "| Timestamp | Ticket | Status | Notes |\n"
            "|-----------|--------|--------|-------|\n"
        )
    with JOURNAL.open("a") as f:
        f.write(line)


# ---------------------------------------------------------------------------
# Ticket helpers
# ---------------------------------------------------------------------------

def load_ticket(path: Path) -> dict:
    raw = path.read_text()
    # strip frontmatter markers and parse body
    lines = raw.strip().splitlines()
    if lines[0].strip() == "---":
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        body = "\n".join(lines[end + 1:])
        front = "\n".join(lines[1:end])
    else:
        body = raw
        front = ""
    data = yaml.safe_load(front or body)
    return data if isinstance(data, dict) else {}


def save_ticket(ticket: dict, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{ticket['id']}.yaml"
    content = "---\n" + yaml.dump(ticket, default_flow_style=False) + "---\n"
    path.write_text(content)


def closed_ids() -> set:
    return {p.stem for p in TICKETS_CLOSED.glob("*.yaml")}


def dependencies_met(ticket: dict) -> bool:
    deps = ticket.get("depends_on") or []
    done = closed_ids()
    return all(d in done for d in deps)


# ---------------------------------------------------------------------------
# Scheduler: pick next ready ticket
# ---------------------------------------------------------------------------

def next_ready_ticket(specific_id: str | None = None) -> Path | None:
    candidates = sorted(TICKETS_OPEN.glob("*.yaml"))
    for path in candidates:
        t = load_ticket(path)
        if specific_id and t.get("id") != specific_id:
            continue
        if t.get("status") == "open" and dependencies_met(t):
            return path
    return None


# ---------------------------------------------------------------------------
# Executor: call the configured executor endpoint
# ---------------------------------------------------------------------------

def call_executor(ticket: dict) -> dict:
    """
    Calls the executor endpoint (Ollama or OpenAI-compat) with the ticket
    as a structured prompt. Returns {success: bool, output: str, tokens: int}.

    The prompt instructs the executor to follow .clinerules strictly:
    - Read context_files
    - Execute task_steps one at a time
    - Write result to result_path
    - Output ONLY the final YAML result block; nothing else
    """
    import urllib.request

    cfg = settings["executor"]
    endpoint = cfg["endpoint"].rstrip("/")
    fmt = cfg.get("format", "ollama")
    model = cfg.get("model", "")  # empty = Cline picks from UI

    ticket_yaml = yaml.dump(ticket, default_flow_style=False)
    system_prompt = (
        "You are a single-ticket executor operating under .clinerules policy.\n"
        "Follow the first-principles chain: Decompose → Ground Truth → Constraints → "
        "Minimal Transform → Verify.\n"
        "Execute ONLY the task_steps listed in the ticket.\n"
        "Use ONLY the allowed_tools listed.\n"
        "Write the result to result_path.\n"
        "Output the final YAML frontmatter result block only. No narration."
    )
    user_prompt = f"TICKET:\n```yaml\n{ticket_yaml}\n```\nExecute this ticket now."

    if fmt == "ollama":
        payload = {
            "model": model or "gemma4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": cfg.get("temperature", 0.2)},
        }
        url = f"{endpoint}/api/chat"
    else:  # openai-compat
        payload = {
            "model": model or "default",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": cfg.get("temperature", 0.2),
            "max_tokens": cfg.get("max_tokens", 4096),
            "stream": False,
        }
        url = f"{endpoint}/chat/completions"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.get('api_key', 'x')}",
        },
        method="POST",
    )
    timeout = cfg.get("timeout_seconds", 180)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except Exception as e:
        return {"success": False, "output": f"ERROR: {e}", "tokens": 0}

    if fmt == "ollama":
        text = body.get("message", {}).get("content", "")
        tokens = body.get("eval_count", 0)
    else:
        text = body["choices"][0]["message"]["content"]
        tokens = body.get("usage", {}).get("completion_tokens", 0)

    return {"success": True, "output": text, "tokens": tokens}


# ---------------------------------------------------------------------------
# Gate runner
# ---------------------------------------------------------------------------

import subprocess

def run_gate(ticket: dict) -> tuple[bool, str]:
    cmd = ticket.get("gate_command", "")
    if not cmd:
        return True, "no gate defined"
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=ROOT
    )
    output = result.stdout + result.stderr
    passed = result.returncode == 0
    return passed, output


# ---------------------------------------------------------------------------
# Main execution loop
# ---------------------------------------------------------------------------

def execute_ticket(path: Path) -> bool:
    """Execute one ticket. Returns True if closed successfully."""
    ticket = load_ticket(path)
    tid = ticket["id"]
    print(f"\n{'='*60}")
    print(f"EXECUTING: {tid} — {ticket.get('title', '')}")
    print(f"{'='*60}")

    # Move to in_progress
    ticket["status"] = "in_progress"
    save_ticket(ticket, TICKETS_IP)
    path.unlink()
    log_event(tid, 0, "scheduler", str(path), "status=in_progress")

    # Call executor
    t_start = datetime.now(timezone.utc)
    result = call_executor(ticket)
    t_end = datetime.now(timezone.utc)
    latency_s = (t_end - t_start).total_seconds()

    log_event(tid, 1, "executor", "endpoint",
              f"success={result['success']} tokens={result['tokens']} latency={latency_s:.1f}s",
              result["tokens"])

    if not result["success"]:
        return _handle_failure(ticket, f"Executor call failed: {result['output']}")

    # Write result to result_path (executor output should be the YAML body)
    result_path = ROOT / ticket.get("result_path", f"output/{tid}-result.yaml")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(result["output"])
    log_event(tid, 2, "write_file", str(result_path), "written")

    # Run gate
    gate_passed, gate_output = run_gate(ticket)
    log_event(tid, 3, "gate", ticket.get("gate_command", ""),
              f"passed={gate_passed}")

    if gate_passed:
        ticket["status"] = "closed"
        ticket["latency_s"] = round(latency_s, 2)
        ticket["tokens_used"] = result["tokens"]
        ip_path = TICKETS_IP / f"{tid}.yaml"
        if ip_path.exists():
            ip_path.unlink()
        save_ticket(ticket, TICKETS_CLOSED)
        journal_entry(tid, "CLOSED", f"latency={latency_s:.1f}s tokens={result['tokens']}")
        print(f"  ✅  {tid} CLOSED ({latency_s:.1f}s, {result['tokens']} tokens)")
        return True
    else:
        ticket["attempts"] = ticket.get("attempts", 0) + 1
        if ticket["attempts"] >= ticket.get("max_retries", MAX_RETRIES):
            return _handle_failure(ticket, f"Gate failed after {ticket['attempts']} attempts:\n{gate_output}")
        # Return to open
        ip_path = TICKETS_IP / f"{tid}.yaml"
        if ip_path.exists():
            ip_path.unlink()
        ticket["status"] = "open"
        save_ticket(ticket, TICKETS_OPEN)
        print(f"  ⚠️  {tid} gate failed (attempt {ticket['attempts']}/{ticket.get('max_retries', MAX_RETRIES)}), retrying")
        return False


def _handle_failure(ticket: dict, reason: str) -> bool:
    tid = ticket["id"]
    ticket["status"] = "failed"
    ticket["failure_reason"] = reason
    ip_path = TICKETS_IP / f"{tid}.yaml"
    if ip_path.exists():
        ip_path.unlink()
    save_ticket(ticket, TICKETS_FAILED)
    journal_entry(tid, "FAILED", reason.splitlines()[0][:80])
    print(f"  ❌  {tid} FAILED: {reason.splitlines()[0][:80]}")
    print(f"     See ISSUE.md and logs/ for details.")
    # Append to ISSUE.md
    issue_path = ROOT / "ISSUE.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    iss_id = f"ISS-{tid}-{ts}"
    with issue_path.open("a") as f:
        f.write(f"\n## {iss_id}\n\n")
        f.write(f"- `status: open`\n")
        f.write(f"- `blocked_on: human`\n")
        f.write(f"- `ticket: {tid}`\n")
        f.write(f"- `reason: {reason.splitlines()[0][:120]}`\n")
        f.write(f"- `action_required: Review failure, fix ticket or context, reset status to open`\n")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one ticket and exit")
    parser.add_argument("--ticket", help="Run a specific ticket ID")
    parser.add_argument("--dry-run", action="store_true", help="Print next ticket without executing")
    args = parser.parse_args()

    print(f"\nMUMPS_Bot runner | session log: {SESSION_LOG.name}")
    print(f"Executor endpoint: {settings['executor']['endpoint']}")

    tickets_run = 0
    while True:
        path = next_ready_ticket(args.ticket)
        if path is None:
            if args.ticket:
                print(f"Ticket {args.ticket} not ready or not found.")
            else:
                print("\nNo more ready tickets. Stack complete.")
            break

        if args.dry_run:
            t = load_ticket(path)
            print(f"Next ready: {t['id']} — {t.get('title', '')}")
            break

        success = execute_ticket(path)
        tickets_run += 1

        if args.once:
            break
        if not success:
            # A failure that exhausted retries halts the loop
            print("\nHalted on failure. Resolve ISSUE.md before continuing.")
            break

    print(f"\nDone. {tickets_run} ticket(s) processed this session.")


if __name__ == "__main__":
    main()
