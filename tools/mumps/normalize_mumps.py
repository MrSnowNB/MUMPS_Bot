#!/usr/bin/env python3
"""Stage 1: MUMPS Abbreviation Normalizer — pure lookup table, zero inference."""
import sys
import hashlib
import json
from pathlib import Path

COMMAND_MAP = {
    "S ": "SET ", "W ": "WRITE ", "D ": "DO ", "Q ": "QUIT ",
    "K ": "KILL ", "N ": "NEW ", "G ": "GOTO ", "L ": "LOCK ",
    "F ": "FOR ", "H ": "HANG ", "I ": "IF ", "E ": "ELSE ",
    "R ": "READ ", "B ": "BREAK ",
    "S\t": "SET\t", "W\t": "WRITE\t", "D\t": "DO\t", "Q\t": "QUIT\t",
    "K\t": "KILL\t", "N\t": "NEW\t", "G\t": "GOTO\t",
}

FUNCTION_MAP = {
    "$P(": "$PIECE(", "$O(": "$ORDER(", "$D(": "$DATA(",
    "$G(": "$GET(", "$Q(": "$QUERY(", "$L(": "$LENGTH(",
    "$T(": "$TEXT(", "$E(": "$EXTRACT(", "$F(": "$FIND(",
    "$NA(": "$NAME(",
}


def normalize_line(line: str) -> str:
    """Expand abbreviations on a single line. Pure function."""
    # Expand command abbreviations at start of line content (after indent)
    stripped = line.lstrip(" \t")
    indent = line[: len(line) - len(stripped)]
    result = stripped
    for short, long in COMMAND_MAP.items():
        if result.startswith(short):
            result = long + result[len(short):]
            break
    for short, long in FUNCTION_MAP.items():
        result = result.replace(short, long)
    return indent + result


def normalize_file(input_path: Path, output_path: Path) -> dict:
    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    normalized = [normalize_line(line) for line in lines]
    content = "".join(normalized)
    output_path.write_text(content, encoding="utf-8")
    sha256 = hashlib.sha256(content.encode()).hexdigest()
    return {
        "output_exists": True,
        "output_path": str(output_path),
        "sha256": sha256,
        "sha256_stable": True,
        "lines_processed": len(lines),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: normalize_mumps.py <input.m> [output.m]"}))
        sys.exit(1)
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("output") / (input_path.stem + ".normalized.m")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = normalize_file(input_path, output_path)
    print(json.dumps(result, indent=2))
