"""Gate test for ROOK-T04: extract calls → output/ROOK-T04-calls.yaml"""
import yaml
from pathlib import Path

OUTPUT = Path("output/ROOK-T04-calls.yaml")


def _load():
    raw = OUTPUT.read_text()
    body = raw.lstrip("-\n")
    return yaml.safe_load(body)


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found"


def test_parses_as_yaml():
    data = _load()
    assert isinstance(data, dict)


def test_calls_key_present():
    data = _load()
    assert "calls" in data, "Top-level key calls missing"


def test_calls_is_list():
    data = _load()
    assert isinstance(data["calls"], list), "calls must be a list"


def test_call_entry_schema():
    data = _load()
    required = {"caller", "callee", "call_type", "line"}
    for entry in data["calls"]:
        missing = required - entry.keys()
        assert not missing, f"Call entry missing keys: {missing}  entry={entry}"
