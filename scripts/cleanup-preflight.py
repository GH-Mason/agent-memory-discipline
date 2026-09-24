#!/usr/bin/env python3
"""cleanup-preflight — fail-safe check that a memory-cleanup job is properly equipped.

The incident postmortem (docs/failure-modes.md) showed the worst failure mode is
a cleanup job that has **silently lost its procedure**: nothing errors, the job
improvises, and load-bearing entries get deleted. This script makes that state
loud. Run it as the first step of every cleanup job; if it fails, the job must
stop — a missing procedure is a stop condition, not a licence to improvise.

Checks performed:
    1. The procedure file exists, is readable, and holds at least --min-chars
       of content (catches deletion and truncation).
    2. The procedure contains every --require substring (defaults check for a
       protect-list and a threshold figure — the two things the loop cannot
       safely run without).
    3. Optionally, a job config JSON has a non-empty skills/attachment field
       (--job-config + --skills-field), catching a detached skill.

Usage:
    python3 cleanup-preflight.py PROCEDURE.md
    python3 cleanup-preflight.py PROCEDURE.md --job-config cron-job.json
    python3 cleanup-preflight.py PROCEDURE.md --require "protect-list" --require "flag for review"

Exit codes:
    0  all checks passed
    2  a check failed or a file could not be read (the cleanup job must NOT run)

On success prints one line; use --quiet to emit nothing (cron-safe). Failure is
always loud, on stderr — silence on the failure path is the bug this exists to
prevent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_REQUIRES = ["protect-list", "%"]
DEFAULT_MIN_CHARS = 200
DEFAULT_SKILLS_FIELD = "skills"


def fail(problems: list[str]) -> int:
    print("cleanup-preflight: FAILED — do not run the cleanup job:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 2


def lookup_dotted(obj: object, dotted: str) -> object:
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="cleanup-preflight",
        description="Fail-safe check that a cleanup job has its procedure and "
                    "skill attached. Run before every cleanup; stop if it fails.",
    )
    p.add_argument("procedure", help="path to the cleanup procedure file")
    p.add_argument("--require", action="append", default=None,
                   help="substring the procedure must contain (repeatable; "
                        f"default: {DEFAULT_REQUIRES})")
    p.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS,
                   help=f"minimum procedure length in chars (default {DEFAULT_MIN_CHARS})")
    p.add_argument("--job-config",
                   help="optional JSON job config to check for an attached skill")
    p.add_argument("--skills-field", default=DEFAULT_SKILLS_FIELD,
                   help=f"dotted key of the skills field in the job config "
                        f"(default {DEFAULT_SKILLS_FIELD!r})")
    p.add_argument("--quiet", action="store_true",
                   help="print nothing on success (failure is always loud)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    problems: list[str] = []

    proc = Path(args.procedure).expanduser()
    if not proc.is_file():
        problems.append(f"procedure file missing: {proc}")
    else:
        try:
            text = proc.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            problems.append(f"procedure unreadable: {proc}: {exc}")
        else:
            stripped = text.strip()
            if len(stripped) < args.min_chars:
                problems.append(
                    f"procedure too short ({len(stripped)} chars < "
                    f"{args.min_chars}) — missing or truncated?")
            for req in (args.require if args.require is not None else DEFAULT_REQUIRES):
                if req.lower() not in stripped.lower():
                    problems.append(
                        f"procedure does not mention {req!r} — the cleanup "
                        f"loop cannot run safely without it")

    if args.job_config:
        cfg_path = Path(args.job_config).expanduser()
        if not cfg_path.is_file():
            problems.append(f"job config missing: {cfg_path}")
        else:
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(f"job config unreadable/invalid JSON: {cfg_path}: {exc}")
            else:
                skills = lookup_dotted(cfg, args.skills_field)
                if not skills:
                    problems.append(
                        f"job config has no skill attached at "
                        f"{args.skills_field!r} — a detached skill is a stop "
                        f"condition, not a licence to improvise")

    if problems:
        return fail(problems)
    if not args.quiet:
        print(f"cleanup-preflight: ok — procedure {proc} intact"
              + ("; skill attached" if args.job_config else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
