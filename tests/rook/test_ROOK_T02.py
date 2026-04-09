"""Gate test for ROOK-T02: list entry points → output/ROOK-T02-entry-points.yaml"""
import yaml
from pathlib import Path

OUTPUT = Path("output/ROOK-T02-entry-points.yaml")


def _load():
    raw = OUTPUT.read_text()
    # strip frontmatter delimiter if present
    body = raw.lstrip("-\n")
    return yaml.safe_load(body)


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found — ROOK-T02 did not write output"


def test_parses_as_yaml():
    data = _load()
    assert isinstance(data, dict)


def test_entry_points_key_present():
    data = _load()
    assert "entry_points" in data, "Top-level key entry_points missing"


def test_entry_points_is_list():
    data = _load()
    assert isinstance(data["entry_points"], list), "entry_points must be a list"


def test_entry_points_nonempty():
    data = _load()
    assert len(data["entry_points"]) > 0, "entry_points list must have at least one item"


def test_entry_point_schema():
    data = _load()
    required = {"label", "line_start", "line_end"}
    for ep in data["entry_points"]:
        missing = required - ep.keys()
        assert not missing, f"Entry point missing keys: {missing}  item={ep}"
