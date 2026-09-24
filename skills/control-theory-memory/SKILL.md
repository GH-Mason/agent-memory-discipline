---
name: control-theory-memory
description: "Memory writes: feedback-replace old, isolate domains."
version: 1.0.0
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [memory, knowledge-management, cybernetics, personal-assistant]
---

# Control-Theory Memory (write-time rules)

Rules for *writing* to a long-running agent's long-term memory. Derived from
*Engineering Cybernetics* (H. S. Tsien) and *Thinking in Systems* (D. H. Meadows).
Cleanup-time rules live in the companion skill `memory-hygiene`.

## Rule 1 — Feedback closing: replace, don't append

A servomechanism corrects by comparing output to the desired state and
rewriting the error away. It does not add a second output beside the first.

**Triggers:** the user corrects a stored fact; new information conflicts with,
supersedes, or refines an entry; the same fact appears twice (near-duplicates
count).

**Procedure:**
- `replace` using a **unique** substring of the old entry (ambiguous matches
  rewrite the wrong entry — the most common failure)
- never `add` a corrected twin: two versions with no tie-break rule is
  divergence, not redundancy
- batch multi-part edits atomically; half-applied state is worse than none
- after writing, verify: old gone, new present, exactly one canonical version

## Rule 2 — Decoupling: separate stores, separated domains

| Kind of information | Destination |
|---|---|
| Stable user preferences / identity / repeated corrections | user profile (hand-maintained) |
| Environment facts / conventions / lessons / tool quirks | working memory |
| Procedures / checklists / workflows | skill or doc files — never facts memory |
| Task progress / IDs / one-off results | session history — store nothing |

Keep life domains in separate entries. One entry = one topic. A mixed entry
cannot be updated later without keeping the irrelevant half.

## Rule 3 — Filtering: stable, not recent

Reject if any apply:
- expires within days (dates, progress, ticket numbers, transient state)
- re-derivable in one search (API details, doc excerpts)
- unverified or low trust — verify first
- emotional / one-off conversational content
- multi-topic — split it or drop it

**Cost test before every write:** *if this vanished tomorrow, would
rediscovering it cost real work?* "No" = the filter firing.

## Rule 4 — Adaptive capacity: fixed budget, periodic compaction

- budget is fixed; compress and merge — **never enlarge to absorb growth**
- operate in the high-signal band (~60–70% observed)
- scheduled audit; silent when nothing to do; report on disk every run
- compact above ~75% toward ~65% (headroom for the next day's writes)

## Rule 5 — Redundancy: the file is the source of truth

- load-bearing conventions live twice: injected memory *and* the rule file
- long-form content lives in files; memory holds a pointer
- a pointer makes weak observability acceptable; without one, a stored file
  may as well not exist

## Kernel checks

**A. Convergence.** After each rewrite, verify state. If the *same topic* needs
correcting twice, the first fix didn't take — root-cause (bad match, wrong
store, leftover duplicate) and fix in one pass. One fact in ≥2 entries =
divergence: merge now.

**B. Debounce.** First sighting of a preference-shaped statement: observe.
Second occurrence or explicit emphasis: store. Latency on doubtful signals
protects certainty on real ones.

**C. Observability.** Injected memory = strong; files = weak and need a
pointer. Audit question for existing entries: *have I actually used this
recently?* No → demote to a note file or delete.

## Write flow

1. Classify (preference / environment / procedure / transient)
2. Route to the correct store
3. Dedupe — replace near-copies, never add beside them
4. Cost-test
5. Commit (atomic batch for multi-part edits)
6. Verify

## Verification

- a "staged, awaiting approval" return means the write has **not** landed;
  only a saved/committed confirmation counts
- after every correction: confirm the old entry is gone and no second version
  survives
