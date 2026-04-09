#!/usr/bin/env bash
# Build tree-sitter-mumps grammar from source for Python 3.13+
# Usage: bash scripts/build_mumps_grammar.sh
#
# This script clones janus-llm/tree-sitter-mumps, patches a missing
# C header, compiles the shared library, and places it where the
# compatibility shim can find it.

set -euo pipefail

GRAMMAR_DIR="vendor/tree-sitter-mumps"
SO_DIR="vendor"
SO_FILE="$SO_DIR/mumps.so"

if [ -f "$SO_FILE" ]; then
    echo "Grammar already built: $SO_FILE"
    echo "Delete it and re-run to rebuild."
    exit 0
fi

echo "=== Cloning tree-sitter-mumps ==="
mkdir -p vendor
if [ ! -d "$GRAMMAR_DIR" ]; then
    git clone https://github.com/janus-llm/tree-sitter-mumps.git "$GRAMMAR_DIR"
fi

echo "=== Patching missing #include <ctype.h> ==="
SCANNER="$GRAMMAR_DIR/src/scanner.c"
if ! grep -q '#include <ctype.h>' "$SCANNER"; then
    sed -i '/#include <wctype.h>/a #include <ctype.h>' "$SCANNER"
    echo "Patched: $SCANNER"
else
    echo "Already patched: $SCANNER"
fi

echo "=== Compiling shared library ==="
gcc -shared -fPIC -O2 \
    -I "$GRAMMAR_DIR/src" \
    "$GRAMMAR_DIR/src/parser.c" \
    "$GRAMMAR_DIR/src/scanner.c" \
    -o "$SO_FILE"

echo "=== Verifying ==="
python3 -c "
import ctypes
lib = ctypes.cdll.LoadLibrary('$SO_FILE')
fn = lib.tree_sitter_mumps
fn.restype = ctypes.c_void_p
ptr = fn()
assert ptr != 0, 'Language pointer is null'
print('OK: mumps.so loads and returns valid language pointer')
"

echo ""
echo "Build complete: $SO_FILE"
echo "The tool scripts will use this via tools/mumps/mumps_grammar.py"
