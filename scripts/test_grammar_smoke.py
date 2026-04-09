#!/usr/bin/env python3
"""Smoke test: verify MUMPS grammar loads and parses."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "mumps"))

from mumps_grammar import get_mumps_language, get_mumps_parser

language = get_mumps_language()
print(f"Language loaded: {language}")

parser = get_mumps_parser()
tree = parser.parse(b"HELLO ; test\n Q\n")

assert tree.root_node.type == "program", \
    f"Expected 'program', got '{tree.root_node.type}'"
assert len(tree.root_node.children) > 0, \
    "Root node has no children"

print(f"Root type: {tree.root_node.type}")
print(f"Children: {len(tree.root_node.children)}")
print("OK: MUMPS grammar loads and parses")

# Write smoke result
out = ROOT / "output" / "BUILD-T01-smoke.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("tree-sitter mumps grammar OK\n")
print(f"Wrote: {out}")
