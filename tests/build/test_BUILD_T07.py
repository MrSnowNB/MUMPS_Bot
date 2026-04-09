"""Gate: BUILD-T07 — runner.py dry-run executes without error."""
from pathlib import Path

OUT = Path("output/BUILD-T07-harness-ok.txt")


def test_output_exists():
    assert OUT.exists(), f"{OUT} not found — BUILD-T07 did not write output"


def test_output_content():
    assert "runner dry-run OK" in OUT.read_text(), \
        "Output must contain 'runner dry-run OK'"


def test_runner_dry_run():
    """Run runner.py --dry-run directly and confirm it exits 0."""
    import subprocess
    result = subprocess.run(
        ["python", "agent/runner.py", "--dry-run"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, \
        f"runner.py --dry-run failed (rc={result.returncode}):\n{result.stderr}"
