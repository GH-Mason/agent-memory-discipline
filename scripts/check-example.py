#!/usr/bin/env python3
"""check-example — keep the documented audit output honest.

examples/README.md quotes memory-audit.py's output verbatim. If the script's
output ever drifts from the documented block, the docs are lying. This script
re-runs the documented command and diffs it against the quoted block. Wired
into CI (.github/workflows/docs-consistency.yml); also runnable locally.

Usage:
    python3 scripts/check-example.py

Exit codes:
    0  documented output matches the script's real output exactly
    1  mismatch (diff on stdout)
    2  usage or file error
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "examples" / "README.md"
STORE = ROOT / "examples" / "example-memory.md"
SCRIPT = ROOT / "scripts" / "memory-audit.py"

MARKER = "Output (verbatim):"


def documented_block(text: str) -> list[str] | None:
    """Return the fenced code block immediately following MARKER."""
    pos = text.find(MARKER)
    if pos == -1:
        return None
    rest = text[pos + len(MARKER):]
    lines = rest.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "```")
    except StopIteration:
        return None
    block: list[str] = []
    for line in lines[start + 1:]:
        if line.strip() == "```":
            return block
        block.append(line)
    return None


def main() -> int:
    if not DOC.is_file() or not STORE.is_file() or not SCRIPT.is_file():
        print("check-example: expected files missing (run from anywhere; paths "
              "are resolved relative to the repo root)", file=sys.stderr)
        return 2

    expected = documented_block(DOC.read_text(encoding="utf-8"))
    if expected is None:
        print(f"check-example: no fenced block after {MARKER!r} in {DOC}",
              file=sys.stderr)
        return 2

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(STORE)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(f"check-example: memory-audit.py exited {proc.returncode}:\n"
              f"{proc.stderr}", file=sys.stderr)
        return 2

    # The doc quotes the command with a relative path; the script echoes
    # whatever path it was given in its header line. Normalise the header.
    actual = proc.stdout.splitlines()
    if actual:
        actual[0] = f"memory-audit  ·  {STORE.relative_to(ROOT)}"

    if actual == expected:
        print("check-example: ok — documented output matches the script "
              "byte-for-byte")
        return 0

    print("check-example: MISMATCH — docs drifted from the script's real "
          "output. Update examples/README.md (or fix the script):")
    print("\n".join(difflib.unified_diff(
        expected, actual,
        fromfile="examples/README.md (documented)",
        tofile="memory-audit.py (actual)",
        lineterm="",
    )))
    return 1


if __name__ == "__main__":
    sys.exit(main())
