"""Gate test for MUM-T01: AST parse output."""
from pathlib import Path
import yaml
import pytest

OUTPUT = Path("output/MUM-T01-ast.yaml")


def load_front(path: Path) -> dict:
    lines = path.read_text().strip().splitlines()
    if lines[0] == "---":
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    return yaml.safe_load(path.read_text()) or {}


def test_output_exists():
    assert OUTPUT.exists(), f"Expected {OUTPUT} to exist after T01 execution"


def test_has_frontmatter():
    text = OUTPUT.read_text().strip()
    assert text.startswith("---"), "File must begin with YAML frontmatter"


def test_has_title_field():
    data = load_front(OUTPUT)
    assert data.get("title"), "Frontmatter must contain non-empty 'title'"


def test_has_ast_key():
    data = load_front(OUTPUT)
    assert "ast" in data or "routine" in data or "nodes" in data, \
        "Output must contain 'ast', 'routine', or 'nodes' key"
