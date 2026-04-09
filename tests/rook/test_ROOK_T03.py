"""Gate test for ROOK-T03: extract globals → output/ROOK-T03-globals.yaml"""
import yaml
from pathlib import Path

OUTPUT = Path("output/ROOK-T03-globals.yaml")


def _load():
    raw = OUTPUT.read_text()
    body = raw.lstrip("-\n")
    return yaml.safe_load(body)


def test_output_exists():
    assert OUTPUT.exists(), f"{OUTPUT} not found"


def test_parses_as_yaml():
    data = _load()
    assert isinstance(data, dict)


def test_globals_key_present():
    data = _load()
    assert "globals" in data, "Top-level key globals missing"


def test_globals_is_dict():
    data = _load()
    assert isinstance(data["globals"], dict), "globals must be a dict"


def test_global_entries_have_reads_writes():
    data = _load()
    for name, meta in data["globals"].items():
        assert "reads" in meta, f"Global {name} missing reads key"
        assert "writes" in meta, f"Global {name} missing writes key"
        assert isinstance(meta["reads"], list), f"Global {name} reads must be list"
        assert isinstance(meta["writes"], list), f"Global {name} writes must be list"
