# Principles, in depth

The five principles and their sources, with the operational detail that made them usable in daily practice.

## 0. The model

Treat memory as a **control system**, not a notebook:

```
observation (conversation) ──► [write filter] ──► memory (stock)
                                    ▲               │
                                    │               ▼
                              correction ◄── [injection: every turn]
                                    │               │
                                    └── [audit loop] ◄── capacity signal
```

Every part of that diagram exists to keep three properties: **convergence** (no oscillation, no divergence), **decoupling** (channels don't corrupt each other), **observability** (what is stored can be retrieved). The principles are just the control actions.

---

## 1. Feedback closing — replace, don't append

**Source.** Engineering Cybernetics — feedback servomechanisms. A feedback loop *reduces* error by comparing actual output against the desired one. Writing an additional entry beside a wrong one is not correction; it is an open loop with two conflicting setpoints.

**Trigger conditions.** Rewrite when:

- the user corrects something previously stored ("that's not what I said", "actually it's X, not Y")
- new information contradicts, supersedes, or refines an existing entry
- the same fact already exists (near-duplicates count — including non-contradictory near-copies)

**Procedure.**

1. Locate the old entry by a *unique substring* — this is the part that goes wrong most often. A substring that matches two entries will silently rewrite the wrong thing.
2. Replace with the complete new version (full text — not a patch).
3. Verify after writing: old gone, new present, exactly one canonical version.
4. Multiple edits in one sitting: submit them as **one atomic batch**, so a mid-way failure cannot leave half-applied state.

**Anti-pattern.** `add`-with-corrected-content. It feels safer (nothing is destroyed), which is exactly why it is dangerous: the system now has two versions and no rule about which one wins.

---

## 2. Decoupling — separate stores, separated domains

**Source.** Engineering Cybernetics — control of multivariable systems. When one channel's actuation leaks into another channel's loop, the system is no longer controllable in the way you designed.

**Store routing.** Four destinations, four different classes of information:

| Class | Destination | Rationale |
|---|---|---|
| User preferences / identity / repeated corrections | user profile | injected every turn; must be stable |
| Environment facts / conventions / lessons / tool quirks | working memory | injected every turn; agent's own model of its world |
| Procedures / checklists / workflows | skill or doc files | loaded *on demand*; would flood the facts layer |
| Task progress / IDs / one-off results | session history | reconstructable by search; worthless as a standing fact |

Getting this wrong in either direction is expensive: a procedure in the facts layer burns budget every turn; a stable preference living only in a doc is invisible when it matters.

**Domain isolation.** Keep separate entries for separate life domains. Mixed entries cannot be updated cleanly later — you end up keeping the irrelevant half to preserve the relevant one.

---

## 3. Filtering — stable, not recent

**Source.** Engineering Cybernetics — filter theory (Wiener, Kalman): extract the signal from noisy observations; the estimate should reject what is transient.

**Rejection rules** (reject if *any* apply):

| Rule | Example |
|---|---|
| Expires within days | "waiting for the 3rd revision", sprint numbers, ticket ids |
| Re-derivable in one search | API specifics, current version numbers, doc quotes |
| Unverified / low trust | "someone said the API supports X" — verify before storing |
| Emotional or one-off | venting, jokes, single-conversation context |
| Multi-topic | split it, or don't store it |

**The cost test.** Before each write: *if this vanished tomorrow, would it cost real work to rediscover?* A "no" is the filter firing.

**Why so strict.** Capacity is a hard constraint in most frameworks; more importantly, recall quality degrades with dilution. The filter *is* the memory system's precision.

---

## 4. Adaptive control — fixed budget, periodic compaction

**Source.** Engineering Cybernetics — self-optimising and adaptive control: measure your own state, move toward a better operating point within fixed constraints.

**Design decisions.**

- **Budget is fixed.** Compress and merge; never enlarge the budget to absorb growth. Enlarging treats the symptom and dilutes recall.
- **Operate in the high-signal band.** Below it you are under-using; above it, entry quality collapses because merging pressure forces bad compromises. The canonical band is defined in [operations.md](operations.md) §2 — do not restate it here.
- **Audit on a schedule.** The audit produces a human-readable report and **stays silent when there's nothing to do** — noise from the maintenance system is still noise.
- **Compaction thresholds.** Trigger and target are defined once, in [operations.md](operations.md) §1 and §4. The headroom between them is for the next day's legitimate writes.

**Who decides what to delete.** Compression decisions need semantic judgment ("is this a high-frequency reference or a historical detail?"), so the audit should be LLM-driven with an explicit procedure — not a heuristic script unattended. Heuristics score; they don't understand load-bearing rules. (Ours did not. See [failure-modes.md](failure-modes.md).)

**Archival is not deletion.** Historical detail that is no longer worth injecting goes to a dated note file; memory keeps a pointer at most.

---

## 5. Redundancy — the file is the source of truth

**Source.** Engineering Cybernetics — redundancy techniques and fault-tolerant systems: single points of failure are design flaws.

- **Load-bearing conventions live twice**: injected memory *and* the rule file (or docs). Memory injection is the hot path; the file survives a memory wipe.
- **Long-form content lives in files.** Memory holds a summary or a pointer, never the full text.
- **Pointers make weak observability acceptable.** A file nobody knows about is dead storage. If memory points at it, it is retrievable — the kernel check for observability, applied directly.

---

## The three kernel checks

These are not principles; they are verifications applied *while operating*, catching the loop errors that pure principles miss.

### A. Convergence — no oscillation

- After every rewrite: verify state (old gone / new present). A "success" return from the write call is necessary but not sufficient if the match was ambiguous. Mechanically: snapshot before the edit, run `scripts/memory-verify.py` on the before/after pair.
- **Same topic corrected twice** ⇒ the first fix didn't take root. Root-cause it immediately: ambiguous match? wrong store? conflicting duplicate left behind? Fix all of it in one pass. This check is only executable if corrections are recorded — keep a one-line-per-correction ledger, or the second correction is invisible (see [operations.md](operations.md) §3).
- **Divergence signal:** one fact appearing in ≥2 entries (including near-duplicates) = the system is diverging; merge and delete the surplus now.

### B. Debounce — second occurrence before commitment

- First sighting of a preference-shaped statement: observe, don't store.
- Second occurrence, or an explicit emphasis from the user: store.
- This is a deliberate latency trade — moving slowly on *doubtful* signals protects the reliability of *certain* ones.

### C. Observability — if it can't be fetched, it isn't stored

- Strongly observable: the injected layer (visible every turn).
- Weakly observable: files (visible only if read). Weak storage requires a pointer in strong storage, or it does not exist.
- Audit question, applied to existing entries: *have I actually used this recently?* No → demote to a note file or delete.

---

## Where the two books each contribute

- **Engineering Cybernetics** → the control structure: feedback closing, decoupling, filtering, adaptation, redundancy, plus the three kernel checks (stability, disturbance rejection, observability are all Tsien's own framing).
- **Thinking in Systems** → the diagnosis language: memory as a stock with no outflow; resilience vs. optimisation for a single condition; leverage points (the *write filter* and the *audit loop* are high-leverage — they shape everything downstream, while individual entries are low-leverage).

The combination is what makes it practical: Tsien tells you the control law; Meadows tells you where to apply it.
