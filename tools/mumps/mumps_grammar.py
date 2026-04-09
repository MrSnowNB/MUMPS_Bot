"""
MUMPS tree-sitter grammar loader — compatibility shim.

Provides get_mumps_language() and get_mumps_parser() for MUMPS, working with:
  - tree-sitter-languages (Python <=3.12, has pre-built MUMPS wheels)
  - Locally compiled mumps.so via tree-sitter >=0.23 (Python 3.13+)

Usage:
    from mumps_grammar import get_mumps_language, get_mumps_parser

    language = get_mumps_language()
    parser = get_mumps_parser()
    tree = parser.parse(b"EN ; entry point")
"""

import ctypes
import warnings
from pathlib import Path

# Locate repo root (two levels up from tools/mumps/)
_ROOT = Path(__file__).resolve().parent.parent.parent
_SO_PATH = _ROOT / "vendor" / "mumps.so"
_CACHED_LANGUAGE = None


def get_mumps_language():
    """Return a tree-sitter Language object for MUMPS."""
    global _CACHED_LANGUAGE
    if _CACHED_LANGUAGE is not None:
        return _CACHED_LANGUAGE

    # Try 1: tree-sitter-languages (works on Python <=3.12)
    try:
        from tree_sitter_languages import get_language
        _CACHED_LANGUAGE = get_language("mumps")
        return _CACHED_LANGUAGE
    except (ImportError, Exception):
        pass

    # Try 2: locally compiled mumps.so
    if not _SO_PATH.exists():
        raise FileNotFoundError(
            f"MUMPS grammar not found at {_SO_PATH}\n"
            f"Run: bash scripts/build_mumps_grammar.sh"
        )

    from tree_sitter import Language

    lib = ctypes.cdll.LoadLibrary(str(_SO_PATH))
    fn = lib.tree_sitter_mumps
    fn.restype = ctypes.c_void_p
    lang_ptr = fn()

    if lang_ptr == 0 or lang_ptr is None:
        raise RuntimeError("tree_sitter_mumps() returned null pointer")

    # Suppress the int-argument deprecation warning in tree-sitter >=0.23
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _CACHED_LANGUAGE = Language(lang_ptr)

    return _CACHED_LANGUAGE


def get_mumps_parser():
    """Return a tree-sitter Parser configured for MUMPS."""
    from tree_sitter import Parser

    language = get_mumps_language()
    parser = Parser(language)
    return parser
