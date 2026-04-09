"""BUILD-T01 gate: verify MUMPS grammar loads and parses."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def test_smoke_file_exists():
    smoke = ROOT / "output" / "BUILD-T01-smoke.txt"
    assert smoke.exists(), f"Missing: {smoke}"
    content = smoke.read_text().strip()
    assert "OK" in content, f"Unexpected content: {content}"

def test_mumps_grammar_loads():
    sys.path.insert(0, str(ROOT / "tools" / "mumps"))
    from mumps_grammar import get_mumps_parser
    parser = get_mumps_parser()
    tree = parser.parse(b"EN ; entry\n S X=1\n Q\n")
    assert tree.root_node.type == "program"
    assert len(tree.root_node.children) > 0
