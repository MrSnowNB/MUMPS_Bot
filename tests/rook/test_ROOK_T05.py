"""Gate test for ROOK-T05: AST queries → output/ROOK-T05-queries.yaml"""
import yaml
from pathlib import Path

OUTPUT = Path("output/ROOK-T05-queries.yaml")
REQUIRED_QUERY_KEYS = {"lock_statements", "goto_commands", "postconditionals"}


def _load():
    raw = OUTPUT.read_text()
    body = raw.lstrip("-\n")
    return yaml.safe_load(body)


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found"


def test_parses_as_yaml():
    data = _load()
    assert isinstance(data, dict)


def test_queries_key_present():
    data = _load()
    assert "queries" in data, "Top-level key queries missing"


def test_query_subkeys_present():
    data = _load()
    queries = data["queries"]
    missing = REQUIRED_QUERY_KEYS - queries.keys()
    assert not missing, f"queries dict missing keys: {missing}"


def test_query_values_are_lists():
    data = _load()
    for k in REQUIRED_QUERY_KEYS:
        assert isinstance(data["queries"][k], list), f"queries.{k} must be a list"


def test_query_entry_schema():
    data = _load()
    for k in REQUIRED_QUERY_KEYS:
        for entry in data["queries"][k]:
            assert "line" in entry and "text" in entry, \
                f"Entry in queries.{k} missing line or text: {entry}"
