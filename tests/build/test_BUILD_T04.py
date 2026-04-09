"""Gate: BUILD-T04 — extract_globals.py and extract_calls.py produce correct JSON."""
import json
from pathlib import Path

GLOBALS_OUT = Path("output/sample-globals.json")
CALLS_OUT   = Path("output/sample-calls.json")


def test_globals_exists():
    assert GLOBALS_OUT.exists(), f"{GLOBALS_OUT} not found"


def test_globals_is_dict():
    data = json.loads(GLOBALS_OUT.read_text())
    assert isinstance(data, dict), "globals output must be a JSON dict"


def test_globals_entry_schema():
    data = json.loads(GLOBALS_OUT.read_text())
    for name, meta in data.items():
        assert "reads"  in meta, f"Global {name} missing reads"
        assert "writes" in meta, f"Global {name} missing writes"
        assert isinstance(meta["reads"],  list), f"Global {name} reads must be list"
        assert isinstance(meta["writes"], list), f"Global {name} writes must be list"


def test_calls_exists():
    assert CALLS_OUT.exists(), f"{CALLS_OUT} not found"


def test_calls_is_list():
    data = json.loads(CALLS_OUT.read_text())
    assert isinstance(data, list), "calls output must be a JSON list"


def test_calls_schema():
    data = json.loads(CALLS_OUT.read_text())
    required = {"caller", "callee", "call_type", "line"}
    for entry in data:
        missing = required - entry.keys()
        assert not missing, f"Call entry missing keys {missing}: {entry}"
