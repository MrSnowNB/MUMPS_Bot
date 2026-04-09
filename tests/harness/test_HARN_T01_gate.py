"""
tests/harness/test_HARN_T01_gate.py
Gate test for HARN-T01.
Rook runs this via: pytest -q tests/harness/test_HARN_T01_gate.py
"""
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_harn_t01_output_exists():
    p = os.path.join(REPO_ROOT, "output", "HARN-T01.txt")
    assert os.path.isfile(p), "output/HARN-T01.txt does not exist"


def test_harn_t01_output_content():
    p = os.path.join(REPO_ROOT, "output", "HARN-T01.txt")
    with open(p) as f:
        content = f.read().strip()
    assert content == "harness-ok", f"Expected 'harness-ok', got: {repr(content)}"
