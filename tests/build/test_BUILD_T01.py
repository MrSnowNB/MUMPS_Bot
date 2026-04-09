"""Gate: BUILD-T01 — tree-sitter-languages mumps grammar loads."""
from pathlib import Path

OUT = Path("output/BUILD-T01-smoke.txt")


def test_smoke_file_exists():
    assert OUT.exists(), f"{OUT} not found — BUILD-T01 did not write output"


def test_smoke_file_content():
    assert "tree-sitter-languages OK" in OUT.read_text(), \
        "Smoke file must contain 'tree-sitter-languages OK'"


def test_grammar_loads_directly():
    """Directly verify import works in this pytest process."""
    from tree_sitter_languages import get_language, get_parser  # noqa
    lang = get_language("mumps")
    parser = get_parser("mumps")
    tree = parser.parse(b"HELLO ; test")
    assert tree.root_node is not None
