#!/usr/bin/env python3
"""
benchmark.py — swap models and score a full ticket stack run.

Usage:
    python agent/benchmark.py --models gemma4 qwen3:8b llama3.3
    python agent/benchmark.py --models gemma4 --stack tickets/open/
    python agent/benchmark.py --report             # print last benchmark report

For each model:
    1. Reset tickets/open/ from backup (tickets/bench_reset/)
    2. Run the full stack via runner.py
    3. Collect scores: gate_pass_rate, avg_latency_s, total_tokens, ticket_fail_count
    4. Write results to output/benchmark-<timestamp>.yaml
    5. Print comparison table
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)
BENCH_RESET = ROOT / "tickets" / "bench_reset"  # snapshot of clean open tickets


def snapshot_tickets():
    """Save current tickets/open/ as bench_reset baseline if not already saved."""
    open_dir = ROOT / "tickets" / "open"
    if not BENCH_RESET.exists():
        shutil.copytree(open_dir, BENCH_RESET)
        print(f"Baseline snapshot saved to {BENCH_RESET}")


def reset_stack():
    """Restore tickets/open/ from bench_reset. Clear closed/failed/in_progress."""
    for subdir in ["open", "closed", "failed", "in_progress"]:
        d = ROOT / "tickets" / subdir
        for f in d.glob("*.yaml"):
            f.unlink()
    if BENCH_RESET.exists():
        for f in BENCH_RESET.glob("*.yaml"):
            shutil.copy(f, ROOT / "tickets" / "open" / f.name)
    # Clear output artefacts from prior run
    for f in OUTPUT.glob("MUM-T*.yaml"):
        f.unlink(missing_ok=True)
    for f in OUTPUT.glob("MUM-T*.md"):
        f.unlink(missing_ok=True)


def patch_model(model_name: str):
    """Temporarily set executor.model in settings.yaml."""
    cfg_path = ROOT / "settings.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["executor"]["model"] = model_name
    cfg_path.write_text(yaml.dump(cfg, default_flow_style=False))


def run_stack() -> dict:
    """Run runner.py to completion. Return stats parsed from session log."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "agent" / "runner.py")],
        capture_output=True, text=True, cwd=ROOT
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])

    # Parse latest session log
    logs = sorted((ROOT / "logs").glob("session_*.jsonl"))
    if not logs:
        return {"gate_pass_rate": 0, "avg_latency_s": 0,
                "total_tokens": 0, "ticket_fail_count": 0, "tickets_closed": 0}

    events = []
    for line in logs[-1].read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    gate_events = [e for e in events if e["tool"] == "gate"]
    passed = sum(1 for e in gate_events if "passed=True" in e["result"])
    rate = (passed / len(gate_events)) if gate_events else 0

    exec_events = [e for e in events if e["tool"] == "executor"]
    latencies = []
    tokens_total = 0
    for e in exec_events:
        for part in e["result"].split():
            if part.startswith("latency="):
                try:
                    latencies.append(float(part.split("=")[1].rstrip("s")))
                except ValueError:
                    pass
            if part.startswith("tokens="):
                try:
                    tokens_total += int(part.split("=")[1])
                except ValueError:
                    pass

    closed_count = len(list((ROOT / "tickets" / "closed").glob("*.yaml")))
    failed_count = len(list((ROOT / "tickets" / "failed").glob("*.yaml")))

    return {
        "gate_pass_rate": round(rate, 3),
        "avg_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "total_tokens": tokens_total,
        "tickets_closed": closed_count,
        "ticket_fail_count": failed_count,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["gemma4"],
                        help="Model names as known to Ollama (e.g. gemma4 qwen3:8b)")
    parser.add_argument("--report", action="store_true",
                        help="Print the most recent benchmark report")
    args = parser.parse_args()

    if args.report:
        reports = sorted(OUTPUT.glob("benchmark-*.yaml"))
        if not reports:
            print("No benchmark reports found.")
            return
        print(reports[-1].read_text())
        return

    snapshot_tickets()
    results = {}

    for model in args.models:
        print(f"\n{'#'*60}")
        print(f"# Benchmarking model: {model}")
        print(f"{'#'*60}")
        reset_stack()
        patch_model(model)
        stats = run_stack()
        stats["model"] = model
        stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        results[model] = stats

    # Restore settings without a model pin
    cfg_path = ROOT / "settings.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["executor"].pop("model", None)
    cfg_path.write_text(yaml.dump(cfg, default_flow_style=False))

    # Write report
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = OUTPUT / f"benchmark-{ts}.yaml"
    report = {
        "title": "Model Benchmark Report",
        "version": "1.0",
        "generated": ts,
        "results": results,
    }
    report_path.write_text("---\n" + yaml.dump(report, default_flow_style=False) + "---\n")
    print(f"\nReport written: {report_path}")

    # Print comparison table
    print("\n=== BENCHMARK RESULTS ===")
    print(f"{'Model':<25} {'Closed':>6} {'Failed':>6} {'Pass%':>7} {'Avg Lat':>9} {'Tokens':>8}")
    print("-" * 65)
    for model, s in results.items():
        rate_pct = f"{s['gate_pass_rate']*100:.1f}%"
        print(f"{model:<25} {s['tickets_closed']:>6} {s['ticket_fail_count']:>6} "
              f"{rate_pct:>7} {s['avg_latency_s']:>8.1f}s {s['total_tokens']:>8}")


if __name__ == "__main__":
    main()
