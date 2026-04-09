"""Gate test for MUM-T02: entry point listing."""
from pathlib import Path
import yaml
import pytest

OUTPUT = Path("output/MUM-T02-entry-points.yaml")


def load_front(path: Path) -> dict:
    lines = path.read_text().strip().splitlines()
    if lines[0] == "---":
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    return yaml.safe_load(path.read_text()) or {}


def test_output_exists():
    assert OUTPUT.exists()


def test_has_frontmatter():
    assert OUTPUT.read_text().strip().startswith("---")


def test_has_entry_points_key():
    data = load_front(OUTPUT)
    assert "entry_points" in data, "Must contain 'entry_points' key"


def test_entry_points_non_empty():
    data = load_front(OUTPUT)
    ep = data.get("entry_points", [])
    assert isinstance(ep, list) and len(ep) > 0, "entry_points must be a non-empty list"
