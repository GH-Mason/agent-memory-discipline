# Operations — numbers, loops, guardrails

Everything in this file is a **starting point to tune**, not a default to trust. See the claim ceiling in the README.

## 1. Budgets

| Store | Budget (chars) | Maintained by |
|---|---|---|
| Working memory | ~4,000 | automated audit + manual |
| User profile | ~2,000 | **manual only** |
| Note files | unbounded | archive, never injected |

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

Steps 3 and 6 are the two that get skipped under time pressure — and produce 90% of the corruption. If you automate anything, automate the verification.

## 4. The cleanup loop

### Schedule

- Nightly is appropriate when usage grows daily (early adoption phase).
- Weekly stabilises later; monthly once growth plateaus.
- Pick a slot away from user-facing activity windows — a maintenance job must never race a live conversation's writes.

### Mode

**LLM-driven with a procedure, not a heuristic script.** The decision "is this entry load-bearing or historical?" needs semantics. A scoring script can only rank; it cannot know that an innocuous one-liner encodes a user directive.

Architecture that worked:

- the job loads a **cleanup skill** (procedure + guardrails) *by name* at run time
- the skill defines threshold, target, protections, and the report format
- the job's final message is silent unless something needs human attention

### Guardrails — non-negotiable

| Guardrail | Why |
|---|---|
| **Explicit protect-list** (rules that must never be deleted). Keep it in the procedure, and re-read it each run | Directives look deletable to a freshness heuristic |
| The cleanup job must **carry its own procedure**. If the job's configuration loses its skill attachment, it must fail safe — not improvise | See the incident: this is exactly how ours drifted |
| **"A copy exists elsewhere" is never a deletion justification.** The injected layer and the skill layer are different roles; a copy in a doc does not make the injected entry redundant | This reasoning deleted a load-bearing directive |
| Threshold and target live in the procedure, not in the job prompt | Stats drift when duplicated |
| Every run **writes a report** to disk, even when nothing is deleted | Undeletable audit trail |
| Deletions are **proposals** when uncertain — "flag for human review" beats a wrong delete | Asymmetric cost: a wrong delete is silent; a flag is harmless |
| The user profile is out of scope. Always | Human-only zone |

### Silent-when-clean

The audit's own output is part of the system's noise budget. Design it to emit nothing when nothing needs doing — including the "I ran fine" message. **If the maintenance system is chatty, the user mutes it, and then real alerts die too.**

## 5. What to log

For at least the first month, log per run:

- occupancy before / after
- entries removed, replaced, merged (count + one-line description)
- entries flagged for human review
- whether the protect-list was read

This log is how you discover that deletions are "correct but unwanted" — the hardest failure class to catch afterwards.

## 6. Interoperation with task work

- Backgrounds, specs and long context belong in files; the prompt carries a *pointer*, not the payload.
- Durable task state (ledgers, IDs, status) belongs in a task ledger file — **not** in long-term memory. Memory is for standing facts; ledgers are for work in flight.
- When a task produces a reusable lesson, update an existing entry (`replace`) rather than appending a new one. Task logs are not memory.

## 7. Failure drills (cheap, do them once)

1. **Ambiguous-match drill.** Write two entries containing a shared substring, then attempt a replace using that substring. Watch what actually gets rewritten. Now you understand why matches must be unique.
2. **Silence drill.** Run the audit when nothing needs cleaning. Confirm it delivers nothing, and that its log still records the run.
3. **Protect-list drill.** Temporarily mark an entry as protected, run the audit with an aggressive threshold, confirm it survives. If it doesn't, the guardrail is decorative.
4. **Recovery drill.** Restore an entry that was deleted a week ago. If this is not possible in a minute or two, your logging isn't good enough yet.
