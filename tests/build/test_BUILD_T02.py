"""Gate: BUILD-T02 — parse_mumps.py produces correct AST JSON from sample.m."""
import json
from pathlib import Path

OUT = Path("output/sample-ast.json")
REQUIRED = {"routine", "filepath", "ast"}


def test_output_exists():
    assert OUT.exists(), f"{OUT} not found"


def test_valid_json():
    data = json.loads(OUT.read_text())
    assert isinstance(data, dict)


def test_required_keys():
    data = json.loads(OUT.read_text())
    missing = REQUIRED - data.keys()
    assert not missing, f"Missing keys: {missing}"


def test_routine_nonempty():
    data = json.loads(OUT.read_text())
    assert data["routine"], "routine must be non-empty string"


def test_ast_nonempty():
    data = json.loads(OUT.read_text())
    assert data["ast"], "ast must be non-empty"


def test_ast_has_children():
    data = json.loads(OUT.read_text())
    assert data["ast"].get("children") or data["ast"].get("type"), \
        "ast root must have type or children"
