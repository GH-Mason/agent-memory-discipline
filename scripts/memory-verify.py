#!/usr/bin/env python3
"""memory-verify — confirm a memory edit landed exactly as intended.

docs/operations.md §3: "steps 3 and 6 [dedupe and verify] are the two that get
skipped under time pressure — and produce 90% of the corruption. If you automate
anything, automate the verification." This is that automation.

Snapshot the file *before* the edit (cp MEMORY.md /tmp/before.md), let the agent
make its edit, then run this script on the before/after pair. It answers three
questions:

    1. Did every entry I intended to remove actually disappear?
       (--expect-removed "unique substring", repeatable)
    2. Did every entry I intended to add actually land?
       (--expect-added "unique substring", repeatable)
    3. Did anything *else* change?  (entry-level diff of everything outside
       the expectations — the catch for ambiguous matches rewriting the wrong
       entry, which is the most common write-side failure)

Usage:
    cp MEMORY.md /tmp/before.md
    # ... agent performs the edit ...
    python3 memory-verify.py /tmp/before.md MEMORY.md \
        --expect-removed "old wording of the corrected fact" \
        --expect-added "new wording"

Exit codes:
    0  all expectations met; no unexpected changes
    1  verification failed (details on stdout)
    2  usage or file error

Entry comparison is whole-entry equality after the same separator splitting and
whitespace normalisation memory-audit.py uses, so a one-character drift inside
an untouched entry is still reported.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_SEPARATOR = "§"


def split_entries(text: str, separator: str) -> list[str]:
    entries: list[str] = []
    buf: list[str] = []
    for line in text.splitlines():
        if line.strip() == separator:
            entries.append("\n".join(buf).strip())
            buf = []
        else:
            buf.append(line)
    entries.append("\n".join(buf).strip())
    return [e for e in entries if e]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="memory-verify",
        description="Verify a memory edit: expected removals gone, expected "
                    "additions present, and nothing else changed.",
    )
    p.add_argument("before", help="snapshot of the memory file before the edit")
    p.add_argument("after", help="the memory file after the edit")
    p.add_argument("--expect-removed", action="append", default=[],
                   help="substring of an entry that must be gone (repeatable)")
    p.add_argument("--expect-added", action="append", default=[],
                   help="substring of an entry that must be present (repeatable)")
    p.add_argument("--separator", default=DEFAULT_SEPARATOR,
                   help=f"line that separates entries (default {DEFAULT_SEPARATOR!r})")
    return p.parse_args(argv)


def read(path_str: str) -> str | None:
    path = Path(path_str).expanduser()
    if not path.is_file():
        print(f"memory-verify: not a file: {path}", file=sys.stderr)
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"memory-verify: cannot read {path}: {exc}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    before_text = read(args.before)
    after_text = read(args.after)
    if before_text is None or after_text is None:
        return 2

    before = split_entries(before_text, args.separator)
    after = split_entries(after_text, args.separator)

    problems: list[str] = []

    for needle in args.expect_removed:
        if any(needle in e for e in after):
            problems.append(f"expected-removed text still present: {needle!r}")

    for needle in args.expect_added:
        if not any(needle in e for e in after):
            problems.append(f"expected-added text not found: {needle!r}")

    # Unexpected changes: entries that differ between before/after while
    # carrying none of the declared substrings on either side.
    declared = args.expect_removed + args.expect_added

    def explained(entry: str) -> bool:
        return any(d in entry for d in declared) if declared else False

    removed_entries = [e for e in before if e not in after]
    added_entries = [e for e in after if e not in before]
    unexpected_removed = [e for e in removed_entries if not explained(e)]
    unexpected_added = [e for e in added_entries if not explained(e)]

    for e in unexpected_removed:
        problems.append(f"unexpected entry removal/rewrite: {e[:80]!r}...")
    for e in unexpected_added:
        problems.append(f"unexpected entry addition/rewrite: {e[:80]!r}...")

    dupes = {e for e in after if after.count(e) > 1}
    for e in dupes:
        problems.append(f"exact duplicate now present: {e[:80]!r}...")

    if problems:
        print("memory-verify: FAILED")
        for p in problems:
            print(f"  - {p}")
        print("\nDo not trust the edit. Inspect the file by hand, fix the "
              "mismatch, and re-run verification (docs/operations.md §3).")
        return 1

    print(f"memory-verify: ok — {len(args.expect_removed)} removal(s), "
          f"{len(args.expect_added)} addition(s) verified; "
          f"{len(removed_entries) + len(added_entries)} entry change(s) total, "
          "none unexpected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
