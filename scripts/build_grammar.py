"""Build tree-sitter-mumps grammar to shared library. Run once."""
import subprocess
from pathlib import Path

GRAMMAR_REPO = "https://github.com/janus-llm/tree-sitter-mumps.git"
BUILD_DIR = Path("tools/mumps/build")
GRAMMAR_DIR = Path("tools/mumps/tree-sitter-mumps")

def build():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if not GRAMMAR_DIR.exists():
        print("Cloning tree-sitter-mumps grammar...")
        subprocess.run(["git","clone","--depth","1",GRAMMAR_REPO,str(GRAMMAR_DIR)], check=True)
    from tree_sitter import Language
    # New API (tree-sitter >= 0.22): build_library is a standalone function
    Language.build_library(str(BUILD_DIR / "mumps.so"), [str(GRAMMAR_DIR)])
    print(f"OK: Grammar compiled → {BUILD_DIR}/mumps.so")

if __name__ == "__main__": build()