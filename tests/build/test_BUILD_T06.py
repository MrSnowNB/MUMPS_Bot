"""Gate: BUILD-T06 — summarize_routine.py and emit_python_stub.py end-to-end."""
import json
from pathlib import Path

SUMMARY_OUT = Path("output/sample-summary.json")
STUB_OUT    = Path("output/sample-stub.py")
SUMMARY_REQUIRED = {
    "routine_name", "entry_point_count", "global_count",
    "call_count", "complexity_flags", "entry_points"
}


def test_summary_exists():
    assert SUMMARY_OUT.exists(), f"{SUMMARY_OUT} not found"


def test_summary_keys():
    data = json.loads(SUMMARY_OUT.read_text())
    missing = SUMMARY_REQUIRED - data.keys()
    assert not missing, f"Summary missing keys: {missing}"


def test_summary_counts_are_ints():
    data = json.loads(SUMMARY_OUT.read_text())
    for k in ("entry_point_count", "global_count", "call_count"):
        assert isinstance(data[k], int), f"{k} must be int"


def test_summary_entry_points_list():
    data = json.loads(SUMMARY_OUT.read_text())
    assert isinstance(data["entry_points"], list)


def test_stub_exists():
    assert STUB_OUT.exists(), f"{STUB_OUT} not found"


def test_stub_has_def():
    text = STUB_OUT.read_text()
    assert "def " in text, "Stub must contain at least one Python function def"


def test_stub_has_docstring():
    text = STUB_OUT.read_text()
    assert '"""' in text, "Stub must contain docstrings"
