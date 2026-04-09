"""Gate test for MUM-T05: audit summary."""
from pathlib import Path
import pytest

OUTPUT = Path("output/MUM-T05-audit.md")


def test_output_exists():
    assert OUTPUT.exists()


def test_has_frontmatter():
    assert OUTPUT.read_text().strip().startswith("---")


def test_has_table():
    assert "|" in OUTPUT.read_text(), "Audit must contain a Markdown table"


def test_references_prior_outputs():
    text = OUTPUT.read_text()
    for ref in ["MUM-T01", "MUM-T02", "MUM-T03", "MUM-T04"]:
        assert ref in text, f"Audit must reference {ref}"
