"""Gate test for ROOK-T01: parse ORQQPL1.m → output/ROOK-T01-ast.json"""
import json
from pathlib import Path

OUTPUT = Path("output/ROOK-T01-ast.json")
REQUIRED_KEYS = {"routine", "filepath", "ast"}


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found — ROOK-T01 did not write output"


def test_output_is_valid_json():
    data = json.loads(OUTPUT.read_text())
    assert isinstance(data, dict), "AST output must be a JSON object"


def test_required_keys_present():
    data = json.loads(OUTPUT.read_text())
    missing = REQUIRED_KEYS - data.keys()
    assert not missing, f"Missing keys in AST JSON: {missing}"


def test_routine_name_is_string():
    data = json.loads(OUTPUT.read_text())
    assert isinstance(data["routine"], str) and data["routine"], "routine must be a non-empty string"


def test_ast_is_nonempty():
    data = json.loads(OUTPUT.read_text())
    assert data["ast"], "ast must be non-empty"
