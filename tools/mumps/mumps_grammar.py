"""
MUMPS tree-sitter grammar loader — zero-order primitive.

## Classification

This is a ZERO-ORDER PRIMITIVE — a shared runtime library, not a callable tool.
It provides a singleton parser factory used internally by first-order pipeline tools.

Do NOT:
  - Call this file directly from the agent or harness
  - Add it to the run_tool.py ALLOWED_TOOLS set
  - Add it to settings.yaml allowed_tools
  - Create a ticket that invokes this file standalone

DO:
  - Import get_mumps_parser() inside parse_mumps.py and any other tool
    that needs to consume raw MUMPS source text

## Future Rook Integration Points (do not implement until Phase 3+)

Scenario A — Hot-cache re-parse:
  Rook holds a persistent get_mumps_parser() instance across the 75-routine
  stack run, eliminating cold grammar loads between routines.

Scenario B — Pre-normalization lint gate:
  Rook calls get_mumps_parser() directly to count ERROR nodes in the raw .m
  file before feeding it to normalize_mumps.py. Routes to human review if
  error_count exceeds a threshold. This is the first planned Rook skill.

Scenario C — Cross-routine structural diffing:
  Rook parses two routines in memory and runs structural similarity queries
  to guide translation of unfamiliar patterns by analogy with known ones.

## Grammar Loading Strategy

Try 1: tree-sitter-languages pip package (Python <=3.12, has pre-built wheels)
Try 2: Locally compiled vendor/mumps.so via scripts/build_mumps_grammar.sh

If neither is available, raises FileNotFoundError with instructions.

## Usage

    from tools.mumps.mumps_grammar import get_mumps_language, get_mumps_parser

    parser = get_mumps_parser()
    tree = parser.parse(b"EN ; entry point\n    QUIT\n")
"""

import ctypes
import warnings
from pathlib import Path

# Locate repo root (two levels up from tools/mumps/)
_ROOT = Path(__file__).resolve().parent.parent.parent
_SO_CANDIDATES = [
    _ROOT / "vendor" / "mumps.so",     # Linux
    _ROOT / "vendor" / "mumps.dylib",  # macOS
]
_CACHED_LANGUAGE = None


def get_mumps_language():
    """Return a tree-sitter Language object for MUMPS (cached singleton)."""
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

    # Try 2: locally compiled mumps.so / mumps.dylib
    so_path = next((p for p in _SO_CANDIDATES if p.exists()), None)
    if so_path is None:
        raise FileNotFoundError(
            f"MUMPS grammar not found.\n"
            f"Checked: {[str(p) for p in _SO_CANDIDATES]}\n"
            f"Run: bash scripts/build_mumps_grammar.sh"
        )

    from tree_sitter import Language

    lib = ctypes.cdll.LoadLibrary(str(so_path))
    fn = lib.tree_sitter_mumps
    fn.restype = ctypes.c_void_p
    lang_ptr = fn()

    if lang_ptr == 0 or lang_ptr is None:
        raise RuntimeError(
            f"tree_sitter_mumps() returned null pointer from {so_path}.\n"
            f"Try re-running: bash scripts/build_mumps_grammar.sh"
        )

    # Suppress the int-argument deprecation warning in tree-sitter >=0.23
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _CACHED_LANGUAGE = Language(lang_ptr)

    return _CACHED_LANGUAGE


def get_mumps_parser():
    """Return a tree-sitter Parser configured for MUMPS (new instance per call)."""
    from tree_sitter import Parser
    language = get_mumps_language()
    parser = Parser(language)
    return parser
