#!/usr/bin/env python3
"""
Validate all JSON and Python artifacts in an output/<ROUTINE>/ directory.
Usage: python scripts/validate_outputs.py output/MPIF001/
"""
import json, ast, sys, pathlib

def validate(output_dir: str):
    p = pathlib.Path(output_dir)
    errors = []

    for f in p.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            if not d:
                errors.append(f"EMPTY JSON: {f}")
        except json.JSONDecodeError as e:
            errors.append(f"INVALID JSON: {f} — {e}")

    for f in p.glob("*.py"):
        try:
            ast.parse(f.read_text())
        except SyntaxError as e:
            errors.append(f"SYNTAX ERROR in {f}: {e}")

    if errors:
        for err in errors: print(f"FAIL: {err}")
        sys.exit(1)
    else:
        print(f"SCHEMA OK: {len(list(p.glob('*.json')))} JSON files, {len(list(p.glob('*.py')))} Python files")

if __name__ == "__main__":
    validate(sys.argv[1])
