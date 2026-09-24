---
name: memory-hygiene
description: "Cleanup-time rules for long-term memory: thresholds, guardrails."
version: 1.0.0
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [memory, hygiene, capacity, cleanup, retention]
---

# Memory Hygiene (cleanup-time rules)

Companion to `control-theory-memory` (write-time rules). This skill governs
the periodic compaction loop.

## Core principles

1. **Memory is a scarce resource, not a free notebook.** Each write occupies
   budget; nothing is auto-reclaimed. A new entry usually means compressing an
   old one — not extending the file.
2. **Density effect.** Recall quality is best in a high-signal band around
   two-thirds occupancy (observed practice, not a measured law; canonical
   band: `docs/operations.md` §2). **Do not enlarge the budget**;
   optimise signal-to-noise instead.
3. **The early phase looks alarming and is normal.** Rapid growth during
   adoption (building the scaffolding) does not justify a bigger budget or
   more aggressive cleaning.
4. **Manual fallback discipline.** Memory inflates on its own; maintenance
   must be scheduled, not reactive — "clean when it breaks" is already too late.
5. **Never touch the user profile.** Hand-maintained store; automation reads,
   never writes.

## Budgets

Canonical values: `docs/operations.md` §1 (single source — do not restate
numbers here; duplicated configuration drifts).

| File | Maintained by |
|---|---|
| Working memory | automated + manual |
| User profile | **manual only** |
| Note files | archive; never injected |

## The cleanup loop

- **Threshold/target:** canonical values live in `docs/operations.md` §1 and
  §4. The headroom between trigger and target covers legitimate writes before
  the next audit.
- **Timing:** a slot away from user-facing activity; never racing a live
  conversation's writes.
- **Mode:** LLM-driven with a written procedure — sentiment-free heuristics
  cannot tell a load-bearing rule from a stale note.
- **Silence:** if below threshold, do nothing and emit nothing. Maintenance
  chatter trains the user to ignore the channel.

## Mandatory guardrails

- **Protect-list** of never-deletable rules, re-read **each run** from the
  procedure (not from the job prompt, not from memory)
- The job must **load this skill by name**; a missing skill is a stop
  condition, not a licence to improvise. A guardrail that can be silently
  detached is documentation, not a guardrail.
- **"A copy exists elsewhere" is never a deletion justification.** The
  injected layer and the on-demand layer play different roles; a copy in a
  doc does not cover the injected role.
- Threshold/target values have **one source** (`docs/operations.md` §1–4) —
  never restated in the job prompt or copied into other files (duplicated
  configuration drifts).
- Every run writes a **report to disk**, even when nothing is deleted.
- Under uncertainty: **flag for review** — a skipped delete costs nothing; a
  wrong delete is silent and usually irreversible.

## Manual cleanup workflow (order matters)

1. Merge entries on the same topic
2. Remove exact duplicates
3. Replace over-long entries with compact versions (move history to a dated
   note file)
4. Archive anything still useful but no longer worth injecting — memory keeps
   a pointer at most
5. Re-check occupancy; stop at the target band

## Guarded against, explicitly

- **Do not delete a rule because "the skill has a copy."** The skill is read
  on demand; the injected entry is seen every turn. Deleting the injection
  while keeping the copy changes behaviour for the worse — see
  `docs/failure-modes.md` in the agent-memory-discipline repository.
- **Do not expand capacity to solve a capacity signal.**
- **Do not fix at 99%.** The buffer exists precisely so the audit is never an
  emergency.
- **Do not write process logs into memory.** "Cleaned N entries today" is
  scratch material.

## Verification after each run

- Confirm deletions match the report; spot-check that no protected entry is gone
- Confirm the report file exists and is non-empty (liveness signal)
- If the same topic was cleaned twice in a row, treat it as an oscillation:
  the entry keeps regrowing — fix the write-side cause, not the symptom
