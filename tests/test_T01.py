"""
Gate test for MUM-T01: AST parse output.
Expects pure JSON output at output/MUM-T01-ast.json.
No YAML frontmatter. No special character escaping required.
"""
import json
from pathlib import Path
import pytest

OUTPUT = Path("output/MUM-T01-ast.json")


def load_ast():
    return json.loads(OUTPUT.read_text())


def test_output_exists():
    assert OUTPUT.exists(), f"Expected {OUTPUT} to exist after MUM-T01 execution"


def test_valid_json():
    try:
        data = load_ast()
    except json.JSONDecodeError as e:
        pytest.fail(f"output/MUM-T01-ast.json is not valid JSON: {e}")


def test_has_routine_key():
    data = load_ast()
    assert "routine" in data, "JSON must contain 'routine' key"
    assert data["routine"], "'routine' must be non-empty"


def test_has_ast_key():
    data = load_ast()
    assert "ast" in data, "JSON must contain 'ast' key"
    assert data["ast"], "'ast' must be non-empty"


def test_has_filepath_key():
    data = load_ast()
    assert "filepath" in data, "JSON must contain 'filepath' key"


def test_ast_has_type_field():
    data = load_ast()
    ast = data["ast"]
    assert isinstance(ast, dict), "'ast' must be a JSON object"
    assert "type" in ast, "'ast' root node must have a 'type' field"
