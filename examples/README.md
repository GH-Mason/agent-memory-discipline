# Example — a sample store and a sample audit

`example-memory.md` is a synthetic working-memory file: 13 entries, no real user,
project, or system. It exists so you can see both the **format** and the
**audit output** before committing your own file.

## Run it

```bash
python3 scripts/memory-audit.py examples/example-memory.md
```

Output (verbatim):

```
memory-audit  ·  examples/example-memory.md

entries    13
chars      2215 / 4000  (55.4%)
threshold  75.0%  →  below — no action needed

review candidates (triage hints, not verdicts):
  [dup ] #5 & #11   overlap 0.67
  [long] #9   449 chars
  [date] #7   2026-03 — verify still current

note: flags are heuristics. Never delete on a flag alone — respect the
protect-list and escalate uncertain cases to a human (docs/operations.md).
```

## What each flag means — and what it does *not* mean

| Flag | Fired on | What to do |
|---|---|---|
| `[dup]` | Entries #5 and #11 — **the same tool quirk, recorded twice in slightly different words** | This is what append-accumulation looks like in practice. Merge into one entry; keep the clearer phrasing. |
| `[long]` | Entry #9, 449 chars — a pointer entry that swallowed its payload instead of pointing at `docs/backup.md` | Compress to a pointer; move the detail to the file it references. |
| `[date]` | Entry #7 mentions `2026-03` | *Verify it is still current* — a date does not make an entry stale, and no date does not make it fresh. |

The `[dup]` and `[long]` flags are deliberate — they demonstrate the two most
common kinds of drift. The `[date]` flag demonstrates a flag that may be a
false alarm: entry #7 is a pointer to a dated note file, which is fine.

**Read the last line of the output every time.** Flags are triage, never
verdicts. The decision — merge, compress, or leave alone — follows the
procedure in [`templates/cleanup-checklist.md`](../templates/cleanup-checklist.md),
with the protect-list applied.

## Try the knobs

```bash
# protect an entry from being flagged at all
python3 scripts/memory-audit.py examples/example-memory.md --protect "never send an email"

# same, but with the list in a file — one pattern per line, single source
python3 scripts/memory-audit.py examples/example-memory.md --protect-file protect-list.txt

# cron-style: prints only when the threshold is crossed
python3 scripts/memory-audit.py examples/example-memory.md --quiet

# tighten the budget to see the trigger fire
python3 scripts/memory-audit.py examples/example-memory.md --limit 2500 --quiet

# machine-readable
python3 scripts/memory-audit.py examples/example-memory.md --json
```

An entry can also protect *itself*: any entry containing the literal tag
`#protect` is exempt from every candidate list, no patterns needed. Prefer the
tag for rules whose wording may evolve — a substring pattern silently stops
matching when the entry is edited; the tag travels with the entry.

## Using it in your own setup

- Point it at *your* store and set `--limit` to your budget. Count semantics:
  characters across entries, separator lines and surrounding whitespace
  excluded — if your host platform counts differently, tune `--limit` until
  the tool's percentage matches what the platform reports.
- Keep it read-only on the delete decision. `memory-audit.py` never edits the
  file; that is by design, not a missing feature.
- Keep your protect-list in one file and pass it with `--protect-file` (or tag
  the entries themselves with `#protect`) so protected entries never enter the
  candidate lists at all.
