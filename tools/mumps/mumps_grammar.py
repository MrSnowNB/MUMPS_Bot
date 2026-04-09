"""
MUMPS tree-sitter grammar loader — compatibility shim.

Provides get_language() and get_parser() for MUMPS, working with both:
  - tree-sitter-languages (Python <=3.12, has pre-built MUMPS wheels)
  - Locally compiled mumps.so via tree-sitter >=0.23 (Python 3.13+)

Usage:
    from mumps_grammar import get_mumps_language, get_mumps_parser

    language = get_mumps_language()
    parser = get_mumps_parser()
    tree = parser.parse(b"EN ; entry\\n Q\\n")
"""

import ctypes
import os
from pathlib import Path

# Locate repo root (two levels up from tools/mumps/)
_ROOT = Path(__file__).resolve().parent.parent.parent
_SO_PATH = _ROOT / "vendor" / "mumps.so"


def get_mumps_language():
    """Return a tree-sitter Language object for MUMPS."""
    # Try 1: tree-sitter-languages (works on Python <=3.12)
    try:
        from tree_sitter_languages import get_language
        return get_language("mumps")
    except (ImportError, Exception):
        pass

    # Try 2: tree-sitter-language-pack (if MUMPS is ever added)
    try:
        from tree_sitter_language_pack import get_language
        return get_language("mumps")
    except (ImportError, Exception):
        pass

    # Try 3: locally compiled mumps.so
    if not _SO_PATH.exists():
        raise FileNotFoundError(
            f"MUMPS grammar not found. Run: bash scripts/build_mumps_grammar.sh\n"
            f"Expected: {_SO_PATH}"
        )

    from tree_sitter import Language

    lib = ctypes.cdll.LoadLibrary(str(_SO_PATH))
    fn = lib.tree_sitter_mumps
    fn.restype = ctypes.c_void_p
    lang_ptr = fn()

    return Language(lang_ptr)


def get_mumps_parser():
    """Return a tree-sitter Parser configured for MUMPS."""
    from tree_sitter import Parser

    language = get_mumps_language()
    parser = Parser(language)
    return parser
