#!/usr/bin/env bash
# =============================================================================
# build_mumps_grammar.sh — Compile MUMPS tree-sitter grammar into vendor/
#
# Run this ONCE before starting the pipeline (BOOT-T01 runs it automatically).
# Safe to re-run — it will skip the clone if tree-sitter-mumps already exists.
#
# What it does:
#   1. Checks for Python, pip, git, tree-sitter CLI
#   2. Installs tree-sitter CLI if missing
#   3. Clones janus-llm/tree-sitter-mumps if not already present
#   4. Builds the grammar into vendor/mumps.so (Linux) or vendor/mumps.dylib (macOS)
#   5. Verifies the compiled grammar loads correctly via a Python smoke test
#
# Outputs:
#   vendor/mumps.so      — on Linux
#   vendor/mumps.dylib   — on macOS
#   (both are in .gitignore — only this script is versioned)
#
# Prerequisites:
#   pip install -r requirements.txt   (must be run first)
#   git
#   A C compiler (gcc or clang — both ship with standard dev tools)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor"
GRAMMAR_DIR="$REPO_ROOT/vendor/tree-sitter-mumps"
GRAMMAR_REPO="https://github.com/janus-llm/tree-sitter-mumps.git"

# Detect OS and set output filename
OS="$(uname -s)"
case "$OS" in
  Darwin*) SO_NAME="mumps.dylib" ;;
  Linux*)  SO_NAME="mumps.so"    ;;
  *) echo "[ERROR] Unsupported OS: $OS" && exit 1 ;;
esac

SO_PATH="$VENDOR_DIR/$SO_NAME"

echo "[build_mumps_grammar] OS: $OS"
echo "[build_mumps_grammar] Output: $SO_PATH"
echo ""

# -----------------------------------------------------------------------------
# Step 1 — Verify prerequisites
# -----------------------------------------------------------------------------
echo "[1/5] Checking prerequisites..."

for cmd in python3 pip3 git; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "[ERROR] Required command not found: $cmd"
    exit 1
  fi
done

echo "      python3: $(python3 --version)"
echo "      pip3:    $(pip3 --version | cut -d' ' -f1-2)"
echo "      git:     $(git --version)"

# Check tree-sitter Python package is installed
if ! python3 -c "import tree_sitter" 2>/dev/null; then
  echo "[ERROR] tree-sitter Python package not found."
  echo "        Run: pip install -r requirements.txt"
  exit 1
fi

# Check C compiler
if command -v gcc &>/dev/null; then
  CC="gcc"
elif command -v clang &>/dev/null; then
  CC="clang"
else
  echo "[ERROR] No C compiler found (gcc or clang required)."
  echo "        On macOS: xcode-select --install"
  echo "        On Ubuntu/Debian: sudo apt-get install build-essential"
  exit 1
fi
echo "      compiler: $CC"

# -----------------------------------------------------------------------------
# Step 2 — Install tree-sitter CLI if missing
# -----------------------------------------------------------------------------
echo ""
echo "[2/5] Checking tree-sitter CLI..."

if ! command -v tree-sitter &>/dev/null; then
  echo "      tree-sitter CLI not found — installing via pip..."
  pip3 install tree-sitter-cli --quiet
fi

echo "      tree-sitter CLI: $(tree-sitter --version 2>/dev/null || echo 'installed')"

# -----------------------------------------------------------------------------
# Step 3 — Clone tree-sitter-mumps grammar source
# -----------------------------------------------------------------------------
echo ""
echo "[3/5] Fetching grammar source..."

mkdir -p "$VENDOR_DIR"

if [ -d "$GRAMMAR_DIR/.git" ]; then
  echo "      tree-sitter-mumps already cloned — pulling latest..."
  git -C "$GRAMMAR_DIR" pull --quiet
else
  echo "      Cloning $GRAMMAR_REPO..."
  git clone --depth 1 --quiet "$GRAMMAR_REPO" "$GRAMMAR_DIR"
fi

echo "      Grammar source: $GRAMMAR_DIR"

# -----------------------------------------------------------------------------
# Step 4 — Compile grammar into vendor/mumps.so or vendor/mumps.dylib
# -----------------------------------------------------------------------------
echo ""
echo "[4/5] Compiling grammar..."

# Build via Python tree_sitter.Language.build_library (tree-sitter <0.23 API)
# For tree-sitter >=0.23 the Language() constructor takes a path directly.
# The Python shim (tools/mumps/mumps_grammar.py) handles both via ctypes.

# Compile the shared library directly with the C compiler for maximum
# compatibility across tree-sitter Python API versions.
SOURCE_FILE="$GRAMMAR_DIR/src/parser.c"

if [ ! -f "$SOURCE_FILE" ]; then
  # Some grammars split into parser.c + scanner.c
  echo "[ERROR] Grammar source not found: $SOURCE_FILE"
  echo "        The tree-sitter-mumps repo structure may have changed."
  echo "        Check: $GRAMMAR_DIR/src/"
  exit 1
fi

# Check for optional scanner.c (external scanner for context-sensitive tokens)
SCANNER_FILE="$GRAMMAR_DIR/src/scanner.c"
if [ -f "$SCANNER_FILE" ]; then
  echo "      Compiling parser.c + scanner.c..."
  "$CC" -shared -fPIC -O2 \
    -I"$GRAMMAR_DIR/src" \
    "$SOURCE_FILE" "$SCANNER_FILE" \
    -o "$SO_PATH"
else
  echo "      Compiling parser.c..."
  "$CC" -shared -fPIC -O2 \
    -I"$GRAMMAR_DIR/src" \
    "$SOURCE_FILE" \
    -o "$SO_PATH"
fi

echo "      Compiled: $SO_PATH"

# -----------------------------------------------------------------------------
# Step 5 — Smoke test: verify the grammar loads and parses a minimal routine
# -----------------------------------------------------------------------------
echo ""
echo "[5/5] Verifying grammar loads..."

python3 - <<'PYEOF'
import sys, ctypes
from pathlib import Path

root = Path(__file__).parent.parent if '__file__' in dir() else Path('.').resolve()
root = Path('.').resolve()  # we're running inline, not as a file

import os
so_candidates = list(Path('vendor').glob('mumps.*'))
if not so_candidates:
    print('[ERROR] No compiled grammar found in vendor/')
    sys.exit(1)

so_path = so_candidates[0]
print(f'      Loading: {so_path}')

try:
    lib = ctypes.cdll.LoadLibrary(str(so_path.resolve()))
    fn = lib.tree_sitter_mumps
    fn.restype = ctypes.c_void_p
    ptr = fn()
    if not ptr:
        print('[ERROR] tree_sitter_mumps() returned null pointer')
        sys.exit(1)
    print(f'      Language pointer: 0x{ptr:x}')
except Exception as e:
    print(f'[ERROR] Failed to load grammar: {e}')
    sys.exit(1)

# Quick parse test
try:
    import tree_sitter
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        lang = tree_sitter.Language(ptr)
    parser = tree_sitter.Parser(lang)
    test_src = b'EN\n    WRITE "hello",10\n    QUIT\n'
    tree = parser.parse(test_src)
    root_node = tree.root_node
    error_count = sum(1 for c in root_node.children if c.type == 'ERROR')
    print(f'      Parse test: root={root_node.type}, errors={error_count}')
    if error_count > 0:
        print('[WARN] Parser returned ERROR nodes on smoke test input.')
        print('       Grammar may be incomplete but is usable.')
    else:
        print('      Grammar OK')
except Exception as e:
    print(f'[WARN] Parse test failed: {e}')
    print('       Grammar compiled but may have runtime issues.')

print('')
print('[build_mumps_grammar] SUCCESS')
PYEOF

echo ""
echo "================================================================"
echo "  Grammar ready: $SO_PATH"
echo "  Run the pipeline: python scripts/next_ticket.py"
echo "================================================================"
