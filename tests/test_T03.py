"""Gate test for MUM-T03: global variable map."""
from pathlib import Path
import yaml
import pytest

OUTPUT = Path("output/MUM-T03-globals.yaml")


def load_front(path):
    lines = path.read_text().strip().splitlines()
    if lines[0] == "---":
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    return yaml.safe_load(path.read_text()) or {}


def test_output_exists():
    assert OUTPUT.exists()


def test_has_globals_key():
    data = load_front(OUTPUT)
    assert "globals" in data


def test_globals_non_empty():
    data = load_front(OUTPUT)
    assert len(data.get("globals", {})) > 0
