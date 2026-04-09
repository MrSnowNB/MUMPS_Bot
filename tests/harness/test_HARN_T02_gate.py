"""
tests/harness/test_HARN_T02_gate.py
Gate test for HARN-T02. Verifies chain from T01 was read and extended.
"""
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_harn_t02_output_exists():
    p = os.path.join(REPO_ROOT, "output", "HARN-T02.txt")
    assert os.path.isfile(p), "output/HARN-T02.txt does not exist"


def test_harn_t02_output_content():
    p = os.path.join(REPO_ROOT, "output", "HARN-T02.txt")
    with open(p) as f:
        content = f.read().strip()
    assert content == "harness-ok-chained", f"Expected 'harness-ok-chained', got: {repr(content)}"
