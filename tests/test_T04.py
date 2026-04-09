"""Gate test for MUM-T04: Python stub emission."""
from pathlib import Path
import pytest

OUTPUT = Path("output/MUM-T04-stub.py.md")


def test_output_exists():
    assert OUTPUT.exists()


def test_has_frontmatter():
    assert OUTPUT.read_text().strip().startswith("---")


def test_has_def():
    assert "def " in OUTPUT.read_text(), "Stub must contain at least one Python function definition"


def test_has_todo():
    assert "TODO" in OUTPUT.read_text(), "Stub must contain at least one TODO marker"
