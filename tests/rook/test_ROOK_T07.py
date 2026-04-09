"""Gate test for ROOK-T07: emit stubs and write ATA log"""
import re
import yaml
from pathlib import Path

STUB_OUTPUT = Path("output/ROOK-T07-stub.py.md")
ATA_LOG = Path("output/ROOK-ATA.md")


def _parse_frontmatter(text):
    """Extract YAML frontmatter between first two --- delimiters."""
    match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    assert match, "File must begin with --- frontmatter block"
    return yaml.safe_load(match.group(1))


def test_stub_file_exists():
    assert STUB_OUTPUT.exists(), f"{STUB_OUTPUT} not found"


def test_stub_has_frontmatter():
    text = STUB_OUTPUT.read_text()
    fm = _parse_frontmatter(text)
    for key in ("routine", "generated_at", "entry_point_count"):
        assert key in fm, f"Frontmatter missing key: {key}"


def test_stub_has_python_code_fence():
    text = STUB_OUTPUT.read_text()
    assert "```python" in text, "Stub file must contain a ```python code fence"
    assert "def " in text, "Stub file must contain at least one Python function def"


def test_ata_log_exists():
    assert ATA_LOG.exists(), f"{ATA_LOG} not found — ROOK-T07 must create or append to it"


def test_ata_log_has_data_row():
    text = ATA_LOG.read_text()
    lines = [l for l in text.splitlines() if l.startswith("|") and "---" not in l]
    # filter out header row
    data_rows = [l for l in lines if "ticket_id" not in l.lower()]
    assert len(data_rows) >= 1, "ROOK-ATA.md must have at least one data row"


def test_ata_row_has_expected_columns():
    text = ATA_LOG.read_text()
    header_line = next(
        (l for l in text.splitlines() if "ticket_id" in l.lower()), None
    )
    assert header_line, "ROOK-ATA.md must have a header row with ticket_id"
    for col in ("ticket_id", "routine", "timestamp", "gate_result"):
        assert col in header_line.lower(), f"ATA header missing column: {col}"
