"""
tests/harness/test_00_smoke.py
Tier 0 — Smoke tests. Run BEFORE Rook starts.
Verify the harness infrastructure is correctly wired.
All tests are pure filesystem / YAML checks. No model involved.
"""
import os
import yaml
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REQUIRED_CLINERULES = [
    "00-policy.md",
    "01-file-format.md",
    "02-ticket-schema.md",
    "03-lifecycle.md",
    "04-failure-handling.md",
    "05-tools.md",
    "06-executor.md",
    "07-stack-runner.md",
    "08-toolbox.md",
    "09-audit.md",
]

REQUIRED_TICKET_DIRS = ["open", "in_progress", "closed", "failed"]

REQUIRED_TICKET_FIELDS = [
    "id", "title", "status", "attempts", "max_retries",
    "depends_on", "allowed_tools", "task_steps",
    "gate_command", "acceptance_criteria", "result_path",
]


def path(*parts):
    return os.path.join(REPO_ROOT, *parts)


def test_settings_loads():
    """settings.yaml must parse and contain required top-level keys."""
    settings_path = path("settings.yaml")
    assert os.path.isfile(settings_path), "settings.yaml not found"
    with open(settings_path) as f:
        s = yaml.safe_load(f)
    for key in ("executor", "tickets", "logging"):
        assert key in s, f"settings.yaml missing required key: {key}"


def test_clinerules_complete():
    """All required .clinerules files must be present."""
    rules_dir = path(".clinerules")
    assert os.path.isdir(rules_dir), ".clinerules/ directory not found"
    present = os.listdir(rules_dir)
    for rule in REQUIRED_CLINERULES:
        assert rule in present, f".clinerules/{rule} is missing"


def test_ticket_dirs_exist():
    """tickets/open/, in_progress/, closed/, failed/ must all exist."""
    for d in REQUIRED_TICKET_DIRS:
        p = path("tickets", d)
        assert os.path.isdir(p), f"tickets/{d}/ directory not found"


def test_journal_writable():
    """logs/luffy-journal.jsonl must exist and be writable."""
    journal = path("logs", "luffy-journal.jsonl")
    assert os.path.exists(journal), "logs/luffy-journal.jsonl does not exist"
    assert os.access(journal, os.W_OK), "logs/luffy-journal.jsonl is not writable"


def _load_ticket_yaml(fpath):
    """Load a ticket YAML file that may use frontmatter --- delimiters."""
    with open(fpath) as f:
        for doc in yaml.safe_load_all(f):
            if isinstance(doc, dict):
                return doc
    return None


def test_open_tickets_valid_yaml():
    """Every file in tickets/open/ must be valid YAML with all required fields."""
    open_dir = path("tickets", "open")
    yaml_files = [f for f in os.listdir(open_dir) if f.endswith(".yaml")]
    assert len(yaml_files) > 0, "No tickets found in tickets/open/"
    for fname in yaml_files:
        fpath = os.path.join(open_dir, fname)
        ticket = _load_ticket_yaml(fpath)
        assert ticket is not None, f"{fname} parsed as empty"
        for field in REQUIRED_TICKET_FIELDS:
            assert field in ticket, f"{fname} missing field: {field}"


def test_dep_graph_no_cycles():
    """Dependency graph across all open tickets must be acyclic."""
    open_dir = path("tickets", "open")
    tickets = {}
    for fname in os.listdir(open_dir):
        if not fname.endswith(".yaml"):
            continue
        t = _load_ticket_yaml(os.path.join(open_dir, fname))
        tickets[t["id"]] = set(t.get("depends_on") or [])

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in tickets}

    def dfs(node):
        color[node] = GRAY
        for dep in tickets.get(node, set()):
            if dep not in color:
                continue  # dep is in closed/done — not a cycle
            if color[dep] == GRAY:
                pytest.fail(f"Cycle detected in dependency graph involving ticket: {dep}")
            if color[dep] == WHITE:
                dfs(dep)
        color[node] = BLACK

    for tid in list(tickets):
        if color[tid] == WHITE:
            dfs(tid)


# Alias for FIX-T02 gate_command compatibility
test_ticket_yaml_valid = test_open_tickets_valid_yaml


def test_start_md_exists():
    """START.md must exist — it is the Rook chat kickoff prompt."""
    assert os.path.isfile(path("START.md")), "START.md not found — Rook has no kickoff prompt"
