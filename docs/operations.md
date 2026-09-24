# Operations — numbers, loops, guardrails

Everything in this file is a **starting point to tune**, not a default to trust. See the claim ceiling in the README.

**Single source:** every number that steers the system (budgets, band, thresholds) is defined in this file and in `scripts/memory-audit.py`'s defaults — nowhere else. Other documents reference this file; they do not restate the numbers. Duplicated configuration drifts (see [failure-modes.md](failure-modes.md)).

## 1. Budgets

| Store | Budget (chars) | Maintained by |
|---|---|---|
| Working memory | ~4,000 | automated audit + manual |
| User profile | ~2,000 | **manual only** |
| Note files | unbounded | archive, never injected |

Budgets are in characters because files are in characters, but host platforms meter in **tokens**. Translate before setting yours: roughly 4 chars/token for English, 1–1.5 chars/token for CJK, mixed text in between. Then tune until the audit's percentage matches what the platform reports.

Two budgets, two maintenance regimes — and the asymmetry is deliberate:

- **Working memory** holds the agent's own model (environment, conventions, lessons). Wrong entries are cheap to fix; automate the audit.
- **User profile** holds the user's identity and preferences. A deletion here is an *interpersonal* error, not just a data error — the user notices when the agent forgets a preference they stated once. **Never let automation edit it.** Automated rewrites of the user profile have a failure mode with no good recovery: the agent silently un-learns something the user will never think to re-state.

## 2. Occupancy band

- Target band: **60–70%** of budget.
- Rationale: observed recall quality. Under-filled wastes nothing but signals untapped capacity; over-filled forces merges that sacrifice precision. The band is where entries stay atomic and specific.

## 3. Write flow (every write)

```
1. Classify    → preference / environment fact / procedure / transient?
                 (procedure → skill file; transient → don't store)
2. Route       → right store? right target?
3. Dedupe      → does a near-copy already exist?
                 yes → replace it (never add beside it)
4. Cost test   → "if this vanished, would rediscovery cost real work?"
5. Commit      → single atomic batch for multi-part edits
6. Verify      → old gone / new present / exactly one canonical version
```

Steps 3 and 6 are the two that get skipped under time pressure — and produce 90% of the corruption. If you automate anything, automate the verification: snapshot the file before the edit, then run `scripts/memory-verify.py` on the before/after pair with the expected removals and additions declared. It fails loudly if anything *else* changed — the ambiguous-match failure made mechanical.

Keep a **correction ledger** (one line per correction: date, topic, what changed). The convergence kernel check — "same topic corrected twice ⇒ root-cause it" — is only executable if corrections are recorded; without the ledger, the second correction is invisible.

## 4. The cleanup loop

### Schedule

- Nightly is appropriate when usage grows daily (early adoption phase).
- Weekly stabilises later; monthly once growth plateaus.
- Pick a slot away from user-facing activity windows — a maintenance job must never race a live conversation's writes.

### Mode

**LLM-driven with a procedure, not a heuristic script.** The decision "is this entry load-bearing or historical?" needs semantics. A scoring script can only rank; it cannot know that an innocuous one-liner encodes a user directive.

### Thresholds (canonical)

- **Trigger:** compact when occupancy exceeds **~75%**.
- **Target:** compress to **~65%** — the 10-point headroom covers the next day's legitimate writes, so the audit is never an emergency.
- These values are referenced by other documents; they are *restated* nowhere.

Architecture that worked:

- the job loads a **cleanup skill** (procedure + guardrails) *by name* at run time
- **preflight first:** the job starts with `scripts/cleanup-preflight.py`, which fails loudly if the procedure is missing, truncated, or the skill attachment is empty. A missing procedure stops the run — it never licences improvisation (this is the incident's fix #1, made executable)
- the skill references the canonical threshold values above, the protections, and the report format
- the job's final message is silent unless something needs human attention

### Guardrails — non-negotiable

| Guardrail | Why |
|---|---|
| **Explicit protect-list** (rules that must never be deleted). Keep it in the procedure, and re-read it each run — feed it to the audit via `--protect-file` so the list has exactly one source. For rules that must survive even rewording, tag the entry itself with `#protect` (the audit honours the tag regardless of patterns) | Directives look deletable to a freshness heuristic; a substring list that lives in CLI arguments drifts like any duplicated config |
| The cleanup job must **carry its own procedure**, verified by `cleanup-preflight.py` at run start. If the job's configuration loses its skill attachment, it must fail safe — not improvise | See the incident: this is exactly how ours drifted |
| **"A copy exists elsewhere" is never a deletion justification.** The injected layer and the skill layer are different roles; a copy in a doc does not make the injected entry redundant | This reasoning deleted a load-bearing directive |
| Threshold and target live in §1/§4 here, not in the job prompt | Stats drift when duplicated |
| **Snapshot before any destructive run** — a timestamped copy, or `git init` in the memory directory and a commit per run | Makes the recovery drill (§7) trivial; without a snapshot, "restore a week-old entry" is a hope, not a capability |
| Every run **writes a report** to disk, even when nothing is deleted | Undeletable audit trail |
| Deletions are **proposals** when uncertain — "flag for human review" beats a wrong delete | Asymmetric cost: a wrong delete is silent; a flag is harmless |
| The user profile is out of scope. Always | Human-only zone |

One reading note on the audit's `[date]` flags: a date inside an entry means *verify currency*, never *delete*. User directives routinely carry their ruling date ("never email, ruled 2026-09-20") — freshness is not importance.

### Silent-when-clean

The audit's own output is part of the system's noise budget. Design it to emit nothing when nothing needs doing — including the "I ran fine" message. **If the maintenance system is chatty, the user mutes it, and then real alerts die too.**

## 5. What to log

For at least the first month, log per run:

- occupancy before / after
- entries removed, replaced, merged (count + one-line description)
- entries flagged for human review
- whether the protect-list was read
- whether the pre-flight check ran and passed
- the snapshot path (so any deletion is recoverable)

This log is how you discover that deletions are "correct but unwanted" — the hardest failure class to catch afterwards.

## 6. Interoperation with task work

- Backgrounds, specs and long context belong in files; the prompt carries a *pointer*, not the payload.
- Durable task state (ledgers, IDs, status) belongs in a task ledger file — **not** in long-term memory. Memory is for standing facts; ledgers are for work in flight.
- When a task produces a reusable lesson, update an existing entry (`replace`) rather than appending a new one. Task logs are not memory.

## 7. Failure drills (cheap, do them once)

1. **Ambiguous-match drill.** Write two entries containing a shared substring, then attempt a replace using that substring. Watch what actually gets rewritten. Now you understand why matches must be unique.
2. **Silence drill.** Run the audit when nothing needs cleaning. Confirm it delivers nothing, and that its log still records the run.
3. **Protect-list drill.** Temporarily mark an entry as protected (a `--protect` pattern or the in-entry `#protect` tag), run the audit with an aggressive threshold, confirm it survives. If it doesn't, the guardrail is decorative.
4. **Recovery drill.** Restore an entry that was deleted a week ago. If this is not possible in a minute or two, your logging isn't good enough yet. With the snapshot guardrail (§4) in place — a timestamped copy or a git commit per run — this drill should be boring; if it isn't, fix the snapshot before trusting the loop.
