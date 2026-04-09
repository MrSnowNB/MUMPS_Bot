"""Gate test for ROOK-T06: synthesize summary → output/ROOK-T06-summary.yaml"""
import yaml
from pathlib import Path

OUTPUT = Path("output/ROOK-T06-summary.yaml")
REQUIRED_SUMMARY_KEYS = {
    "routine_name", "entry_point_count", "global_count",
    "call_count", "complexity_flags"
}


def _load():
    raw = OUTPUT.read_text()
    body = raw.lstrip("-\n")
    return yaml.safe_load(body)


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found"


def test_parses_as_yaml():
    data = _load()
    assert isinstance(data, dict)


def test_summary_key_present():
    data = _load()
    assert "summary" in data, "Top-level key summary missing"


def test_summary_subkeys_present():
    data = _load()
    missing = REQUIRED_SUMMARY_KEYS - data["summary"].keys()
    assert not missing, f"summary dict missing keys: {missing}"


def test_counts_are_integers():
    data = _load()
    s = data["summary"]
    for key in ("entry_point_count", "global_count", "call_count"):
        assert isinstance(s[key], int), f"{key} must be an integer, got {type(s[key])}"


def test_complexity_flags_is_list():
    data = _load()
    assert isinstance(data["summary"]["complexity_flags"], list), \
        "complexity_flags must be a list"
