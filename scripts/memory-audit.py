#!/usr/bin/env python3
"""memory-audit — occupancy report and review candidates for a markdown memory file.

A read-only triage aid: it never edits your memory file. Flags are hints for a
human (or for an LLM following a written cleanup procedure) — **never delete an
entry just because a flag fired**. See docs/operations.md for the full loop.

Usage:
    python3 memory-audit.py MEMORY.md
    python3 memory-audit.py MEMORY.md --limit 4000 --threshold 75 --target 65
    python3 memory-audit.py MEMORY.md --protect "never email" --quiet
    python3 memory-audit.py MEMORY.md --json

Exit codes:
    0  report produced (regardless of occupancy)
    2  usage or file error

Char counting: characters across entries, separator lines and surrounding
whitespace excluded. Host platforms may count slightly differently — tune
--limit until this tool's percentage matches what your platform reports.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SEPARATOR = "§"
DEFAULT_LIMIT = 4000
DEFAULT_THRESHOLD = 75.0
DEFAULT_TARGET = 65.0
DEFAULT_MAX_ENTRY_CHARS = 400
DEFAULT_DUP_OVERLAP = 0.5
DEFAULT_TOP = 10

_WORD = re.compile(r"[0-9A-Za-z_]{2,}")
_CJK = re.compile(r"[\u4e00-\u9fff]+")
_DATE = re.compile(r"\b(?:19|20)\d{2}\s*[-/.年]\s*\d{1,2}(?:\s*[-/.月]\s*\d{1,2})?")

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "not", "are", "was",
    "you", "your", "its", "it", "is", "of", "to", "in", "on", "at", "as",
    "by", "or", "be", "an", "if", "so", "no", "do", "use", "used",
}


def split_entries(text: str, separator: str) -> tuple[list[str], bool]:
    """Split a memory file into entries on lines consisting of *separator*."""
    entries: list[str] = []
    buf: list[str] = []
    found = False
    for line in text.splitlines():
        if line.strip() == separator:
            found = True
            entries.append("\n".join(buf).strip())
            buf = []
        else:
            buf.append(line)
    entries.append("\n".join(buf).strip())
    return [e for e in entries if e], found


def tokens(text: str) -> set[str]:
    """Tokens for overlap detection: latin words + CJK bigrams.

    Deliberately crude — this is a triage hint, not a similarity engine.
    """
    low = text.lower()
    toks = {w for w in _WORD.findall(low) if w not in _STOPWORDS}
    for run in _CJK.findall(low):
        if len(run) == 1:
            toks.add(run)
        else:
            toks.update(run[i:i + 2] for i in range(len(run) - 1))
    return toks


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def build_report(path: Path, entries: list[str], found: bool, args: argparse.Namespace) -> dict:
    chars = sum(len(e) for e in entries)
    occupancy = (chars / args.limit * 100.0) if args.limit else 0.0
    above = occupancy >= args.threshold

    protect_norms = [p.lower() for p in args.protect]
    protected = {
        i for i, e in enumerate(entries, 1)
        if any(p in e.lower() for p in protect_norms)
    }

    longs = [
        {"entry": i, "chars": len(e)}
        for i, e in enumerate(entries, 1)
        if len(e) > args.max_entry_chars and i not in protected
    ]

    dated = []
    for i, e in enumerate(entries, 1):
        if i in protected:
            continue
        m = _DATE.search(e)
        if m:
            dated.append({"entry": i, "match": m.group(0)})

    toks = [tokens(e) for e in entries]
    dups = []
    for i in range(len(entries)):
        if (i + 1) in protected:
            continue
        for j in range(i + 1, len(entries)):
            if (j + 1) in protected:
                continue
            score = jaccard(toks[i], toks[j])
            if score >= args.dup_overlap:
                dups.append({"a": i + 1, "b": j + 1, "overlap": round(score, 2)})
    dups.sort(key=lambda d: -d["overlap"])

    return {
        "path": str(path),
        "entries": len(entries),
        "chars": chars,
        "limit": args.limit,
        "occupancy_pct": round(occupancy, 1),
        "threshold_pct": args.threshold,
        "target_pct": args.target,
        "above_threshold": above,
        "protected_count": len(protected),
        "separator_found": found,
        "candidates": {
            "duplicates": dups[: args.top],
            "long_entries": sorted(longs, key=lambda d: -d["chars"])[: args.top],
            "dated_entries": dated[: args.top],
        },
    }


def render_text(rep: dict, quiet: bool) -> str:
    if quiet:
        if not rep["above_threshold"]:
            return ""
        c = rep["candidates"]
        n = len(c["duplicates"]) + len(c["long_entries"]) + len(c["dated_entries"])
        return (
            f"memory-audit: {rep['occupancy_pct']}% of {rep['limit']} "
            f"(threshold {rep['threshold_pct']}%) — compact toward "
            f"{rep['target_pct']}%. {n} review candidate(s)."
        )

    out = [
        f"memory-audit  ·  {rep['path']}",
        "",
        f"entries    {rep['entries']}",
        f"chars      {rep['chars']} / {rep['limit']}  ({rep['occupancy_pct']}%)",
    ]
    if rep["above_threshold"]:
        out.append(
            f"threshold  {rep['threshold_pct']}%  →  ABOVE — compact toward "
            f"{rep['target_pct']}%"
        )
    else:
        out.append(f"threshold  {rep['threshold_pct']}%  →  below — no action needed")
    if rep["protected_count"]:
        out.append(f"protected  {rep['protected_count']} entr(y/ies) matched --protect")
    if not rep["separator_found"]:
        out.append("note       no separator lines found — file treated as one entry")

    c = rep["candidates"]
    out.append("")
    if not (c["duplicates"] or c["long_entries"] or c["dated_entries"]):
        out.append("review candidates: none")
    else:
        out.append("review candidates (triage hints, not verdicts):")
        for d in c["duplicates"]:
            out.append(f"  [dup ] #{d['a']} & #{d['b']}   overlap {d['overlap']}")
        for d in c["long_entries"]:
            out.append(f"  [long] #{d['entry']}   {d['chars']} chars")
        for d in c["dated_entries"]:
            out.append(f"  [date] #{d['entry']}   {d['match']} — verify still current")

    out.append("")
    out.append(
        "note: flags are heuristics. Never delete on a flag alone — respect the\n"
        "protect-list and escalate uncertain cases to a human (docs/operations.md)."
    )
    return "\n".join(out)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="memory-audit",
        description="Occupancy report + review candidates for a markdown memory file.",
    )
    p.add_argument("path", help="path to the memory file (e.g. MEMORY.md)")
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                   help=f"character budget (default {DEFAULT_LIMIT})")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help=f"occupancy %% that triggers compaction (default {DEFAULT_THRESHOLD})")
    p.add_argument("--target", type=float, default=DEFAULT_TARGET,
                   help=f"occupancy %% to compact toward (default {DEFAULT_TARGET})")
    p.add_argument("--separator", default=DEFAULT_SEPARATOR,
                   help=f"line that separates entries (default {DEFAULT_SEPARATOR!r})")
    p.add_argument("--protect", action="append", default=[],
                   help="substring marking an entry as never-touch (repeatable)")
    p.add_argument("--max-entry-chars", type=int, default=DEFAULT_MAX_ENTRY_CHARS,
                   help=f"flag entries longer than this (default {DEFAULT_MAX_ENTRY_CHARS})")
    p.add_argument("--dup-overlap", type=float, default=DEFAULT_DUP_OVERLAP,
                   help=f"flag entry pairs with token overlap >= this (default {DEFAULT_DUP_OVERLAP})")
    p.add_argument("--top", type=int, default=DEFAULT_TOP,
                   help=f"cap per candidate list (default {DEFAULT_TOP})")
    p.add_argument("--quiet", action="store_true",
                   help="print only when above threshold (for cron use)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.path).expanduser()
    if not path.is_file():
        print(f"memory-audit: not a file: {path}", file=sys.stderr)
        return 2
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"memory-audit: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    entries, found = split_entries(text, args.separator)
    rep = build_report(path, entries, found, args)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0

    rendered = render_text(rep, args.quiet)
    if rendered:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
