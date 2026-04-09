"""
tests/harness/test_HARN_T03_gate.py
Gate test for HARN-T03. Verifies valid JSON summary with chain_valid == True.
"""
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_harn_t03_output_exists():
    p = os.path.join(REPO_ROOT, "output", "HARN-T03.json")
    assert os.path.isfile(p), "output/HARN-T03.json does not exist"


def test_harn_t03_valid_json():
    p = os.path.join(REPO_ROOT, "output", "HARN-T03.json")
    with open(p) as f:
        data = json.load(f)  # raises if invalid JSON
    assert "t01" in data, "HARN-T03.json missing key: t01"
    assert "t02" in data, "HARN-T03.json missing key: t02"
    assert "chain_valid" in data, "HARN-T03.json missing key: chain_valid"


def test_harn_t03_chain_valid_true():
    p = os.path.join(REPO_ROOT, "output", "HARN-T03.json")
    with open(p) as f:
        data = json.load(f)
    assert data["chain_valid"] is True, f"chain_valid is not True: {data}"


def test_harn_t03_values_correct():
    p = os.path.join(REPO_ROOT, "output", "HARN-T03.json")
    with open(p) as f:
        data = json.load(f)
    assert data["t01"].strip() == "harness-ok"
    assert data["t02"].strip() == "harness-ok-chained"
