# Cleanup checklist

The human-readable procedure. Run in order; the order matters (verify before destructive steps, destructive steps last).

## Before touching anything

- [ ] Run `scripts/cleanup-preflight.py` against this procedure (and the job config, if the run is scheduled). **If it fails, stop** — a missing or truncated procedure is a stop condition, not a licence to improvise
- [ ] **Snapshot the store** (timestamped copy, or a git commit if the memory directory is versioned). No snapshot, no destructive run
- [ ] Read the **protect-list** from the procedure (do not work from memory of it); feed it to the audit with `--protect-file` so the list has one source
- [ ] Confirm scope: working memory only — **user profile is out of scope**
- [ ] Read current occupancy; if below the trigger threshold → stop, done
- [ ] Locate the report path so the run can be logged even if nothing is changed

## Compress, in this order

1. [ ] **Merge** entries on the same topic (same subject split across entries)
2. [ ] **Remove** exact duplicates
3. [ ] **Replace** over-long entries with compact versions — keep the core; move history to a dated note file
4. [ ] **Flag, don't delete**: anything uncertain → report as "for review"
5. [ ] Re-check occupancy after each class of edit; stop when the target band is reached

## Never

- [ ] Delete an entry because "a copy exists in a skill or a doc" — different role, not redundancy
- [ ] Delete anything on the protect-list
- [ ] Enlarge the budget as a fix
- [ ] Touch the user profile
- [ ] Delete silently without a report on disk

## After

- [ ] Verify the edits mechanically: `scripts/memory-verify.py <snapshot> <store>` with the intended removals/additions declared — it fails if anything *else* changed
- [ ] Verify a sample of edits by eye: old entries gone, new entries present, no duplicate pairs
- [ ] Write the run log: occupancy before/after; entries removed / replaced / merged; flagged items; snapshot path
- [ ] If anything was deleted: one-line description per deletion, in the report
- [ ] Stay silent on the messaging channel unless something needs a human decision

## Escalate to the human when

- [ ] Compaction would need to cut into the protect-list to reach target
- [ ] Two entries contradict each other and neither looks stale (needs a real decision)
- [ ] The same topic keeps being re-corrected (an oscillation — root-cause it, don't re-fix)
- [ ] Budget pressure is structural (not a one-off spike): the entry set is too fine-grained for the budget, and the fix is a design change, not another cleanup
