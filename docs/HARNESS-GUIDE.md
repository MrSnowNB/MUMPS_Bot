---
title: Harness Guide
version: "1.0"
last_updated: "2026-04-09"
---

# MUMPS_Bot Harness Guide

## Architecture

```
tickets/open/     ← YAML ticket files (DAG nodes)
      ↓ scheduler.py picks next ready ticket (all deps in tickets/closed/)
      ↓ runner.py calls executor endpoint, writes result, runs gate
      ↓ tickets/closed/  (success) | tickets/failed/  (exhausted retries)
      ↓ logs/session_*.jsonl  ← every tool call timestamped
      ↓ logs/journal.md       ← human-readable pass/fail log
```

## Quick Start

```bash
# 1. Install deps
pip install pyyaml pytest

# 2. Confirm Ollama is running with your model loaded
curl http://localhost:11434/api/tags

# 3. Dry-run: see what would execute next
python agent/runner.py --dry-run

# 4. Run one ticket
python agent/runner.py --once

# 5. Run full stack to completion
python agent/runner.py

# 6. Check status
python agent/scheduler.py --status
```

## Swapping Models

Edit `settings.yaml` → `executor.model` to any Ollama model tag:

```yaml
executor:
  endpoint: http://localhost:11434
  format: ollama
  model: qwen3:8b        # change this line
```

Or use the benchmark script to compare multiple models automatically:

```bash
python agent/benchmark.py --models gemma4 qwen3:8b llama3.3
```

## Benchmark Output

After a benchmark run, `output/benchmark-<timestamp>.yaml` contains:

```yaml
results:
  gemma4:
    gate_pass_rate: 0.8
    avg_latency_s: 12.3
    total_tokens: 4820
    tickets_closed: 4
    ticket_fail_count: 1
  qwen3:8b:
    gate_pass_rate: 1.0
    avg_latency_s: 31.7
    total_tokens: 9100
    tickets_closed: 5
    ticket_fail_count: 0
```

**Scoring dimensions:**

| Metric | Meaning | Want |
|--------|---------|------|
| `gate_pass_rate` | Fraction of gate runs that passed | High |
| `avg_latency_s` | Average seconds per ticket | Low |
| `total_tokens` | Token spend for full stack | Low |
| `tickets_closed` | Tickets fully completed | High |
| `ticket_fail_count` | Tickets that exhausted retries | Zero |

## Failure Recovery

If runner halts on a failed ticket:

1. Read `ISSUE.md` for the exact failure reason
2. Read `logs/session_*.jsonl` for the full tool call trace
3. Fix the ticket YAML or the context file
4. Reset the ticket: move `tickets/failed/MUM-TXX.yaml` back to `tickets/open/`,
   set `status: open` and `attempts: 0`
5. Re-run: `python agent/runner.py`

## Adding New Tickets

1. Copy `tickets/template.yaml`
2. Fill all required fields (see template for schema)
3. Set `depends_on` to all ticket IDs that must close first
4. Write the gate test in `tests/test_<ID>.py`
5. Drop into `tickets/open/` — the scheduler picks it up automatically

## Context Window Warning

If executor logs show `latency > 120s` or truncated output:
- Reduce `context_files` list in the ticket
- Split the ticket into two smaller tickets
- Increase `executor.timeout_seconds` in `settings.yaml`
