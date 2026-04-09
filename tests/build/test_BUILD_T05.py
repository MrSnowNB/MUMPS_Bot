"""Gate: BUILD-T05 — query_ast.py produces correct queries JSON from sample.m."""
import json
from pathlib import Path

OUT = Path("output/sample-queries.json")
REQUIRED = {"lock_statements", "goto_commands", "postconditionals"}


def test_output_exists():
    assert OUT.exists(), f"{OUT} not found"


def test_valid_json_dict():
    data = json.loads(OUT.read_text())
    assert isinstance(data, dict)


def test_required_keys():
    data = json.loads(OUT.read_text())
    missing = REQUIRED - data.keys()
    assert not missing, f"Missing keys: {missing}"


def test_values_are_lists():
    data = json.loads(OUT.read_text())
    for k in REQUIRED:
        assert isinstance(data[k], list), f"{k} must be a list, got {type(data[k])}"


def test_entry_schema():
    data = json.loads(OUT.read_text())
    for k in REQUIRED:
        for entry in data[k]:
            assert "line" in entry and "text" in entry, \
                f"Entry in {k} missing line or text: {entry}"
