"""Gate: BUILD-T03 — list_entry_points.py produces correct JSON from sample.m."""
import json
from pathlib import Path

OUT = Path("output/sample-entry-points.json")


def test_output_exists():
    assert OUT.exists(), f"{OUT} not found"


def test_valid_json_list():
    data = json.loads(OUT.read_text())
    assert isinstance(data, list), "Output must be a JSON list"


def test_entry_schema():
    data = json.loads(OUT.read_text())
    required = {"label", "line_start", "line_end"}
    for ep in data:
        missing = required - ep.keys()
        assert not missing, f"Entry point missing keys {missing}: {ep}"


def test_label_is_string():
    data = json.loads(OUT.read_text())
    for ep in data:
        assert isinstance(ep["label"], str) and ep["label"], \
            f"label must be non-empty string: {ep}"
