# Memory Discipline for LLM Agents

*What to write, when to rewrite, how much to keep — and how to clean up a long-running agent's memory without losing what matters.*

Most agent-memory projects focus on **architecture**: vector stores, graph memory, retrieval pipelines, bigger context windows. This repo is about the other half — **discipline**. It documents the operating rules a long-running personal agent has been living under, and the incident that proved why some of them are non-negotiable.

The rules come from mapping two classic texts onto everyday agent behaviour:

| Source | Concepts borrowed |
|---|---|
| **Engineering Cybernetics** — H. S. Tsien (1954) | feedback servomechanisms · decoupled control of multivariable systems · filtering noise out of observations · self-optimising control · adaptive control · redundancy & fault tolerance |
| **Thinking in Systems** — Donella H. Meadows (2008) | stocks & flows · resilience · leverage points · bounded rationality |

> This repo shares *our implementation notes*, not the books' content — see [Sources](#sources).

---

## The failure mode everyone hits

An agent's long-term memory is a **stock with an inflow and no natural outflow**. Every write is cheap; nothing expires on its own. The default trajectories:

- **Append-accumulation.** The user corrects a fact; the agent adds a new note *next to* the old one. Two contradictory entries now coexist, and future retrieval is a coin flip.
- **Capacity creep.** The budget fills up; the intuitive fix is a bigger budget. Recall gets *worse* — the same attention is now spread over more, weaker signals.
- **Unsupervised cleanup.** A maintenance job trims "stale" entries and silently deletes rules that were load-bearing. Ours did exactly that. → [docs/failure-modes.md](docs/failure-modes.md)

The five principles below are the fixes.

---

## Five principles

### 1. Close the feedback loop — replace, don't append

> *Engineering Cybernetics:* a servomechanism compares output to the desired state, derives an error, and corrects. It does not *add* a second output alongside the first.

When the user corrects a stored fact, **rewrite** the entry:

- `replace` the old entry (or `remove` it) — never `add` a corrected twin
- two entries describing the same fact = **divergence**, not redundancy
- after every correction, verify: old entry gone, new entry present, exactly one canonical version

### 2. Decouple — separate stores, separated domains

> *Engineering Cybernetics:* in a multivariable system, each control channel must act without disturbing the others.

Before writing, decide *which* store the fact belongs to:

| Kind of information | Where it goes |
|---|---|
| Stable user preferences, identity, recurring corrections | user-profile store |
| Environment facts, conventions, lessons, tool quirks | agent working memory |
| Reusable procedures, checklists, workflows | **skills / docs** — never facts memory |
| Task progress, IDs, one-off results | **nowhere** — reconstruct from session history |

Keep domains (work / personal / finance / correspondence) in separate entries. One entry = one topic.

### 3. Filter — memory is for the *stable*, not the *recent*

> *Engineering Cybernetics:* filter noisy observations, keep the minimum-variance estimate of the signal that actually matters.

Capacity is finite, so filtering is not optional. Reject on sight:

- anything that expires within days (dates, progress, ticket numbers, transient state)
- anything a single search would re-derive (API details, doc excerpts)
- unverified or low-trust claims — verify first, store later
- emotional venting, one-off conversational content

Ask before every write: *if this vanished, would it actually cost me something?* If no, it's noise.

### 4. Adapt — fixed budget, periodic compaction

> *Engineering Cybernetics* (self-optimising & adaptive control): the system measures itself and corrects toward a better operating point — within its constraints.

- Set an explicit character budget. **Do not enlarge it to solve growth.** Compress and merge instead.
- Keep occupancy in the high-signal band (~60–70% in our experience); a roomy memory dilutes recall.
- Run an automated audit on a schedule; a human-readable report each time; silent when nothing needs doing.
- Thresholds: compact when usage exceeds ~75%, down to ~65% — leave headroom for the next day's writes.

### 5. Redundancy — the file is the source of truth

> *Engineering Cybernetics:* redundancy and fault tolerance keep one failed component from taking down the system.

- Load-bearing conventions live in **two** places (e.g. injected memory *and* the rule file), so one loss is survivable.
- Long-form content lives in files; memory holds only a **pointer** to it.
- Dated, descriptive filenames make every artifact retrievable — observability is a naming discipline too.

---

## Three kernel checks

Most memory bugs are not architectural. They are loop errors:

| Check | Failure it prevents | Practice |
|---|---|---|
| **Convergence** (stability) | *Oscillation* — corrected once, silently reverts next week | After each rewrite verify old-gone/new-present; if the same topic needs correcting **twice**, find the root cause (bad match, wrong store) and fix it in one pass |
| **Debounce** (disturbance rejection) | *Noise capture* — a passing remark becomes permanent policy | Not sure it's stable? Wait for a second occurrence before committing |
| **Observability** | *Dead storage* — saved but never retrievable | Injected memory = strongly observable; files = weakly observable and need a pointer from memory, or they effectively don't exist |

---

## Layout

```
README.md                  this file (English)
README.zh-CN.md            中文版
docs/
  principles.md            the five principles + kernel checks, in depth
  operations.md            numbers, write flow, cleanup loop, guardrail design
  porting.md               install recipes per framework (Claude Code, Codex, Cursor, generic)
  failure-modes.md         anti-patterns + the incident (sanitised)
templates/
  injected-rules.md        the short always-on block to paste into your rules layer
  MEMORY.template.md       starter working-memory file
  USER.template.md         starter user-profile file
  cleanup-checklist.md     the human-readable audit checklist
scripts/
  memory-audit.py          occupancy + review-candidate report (stdlib, read-only)
examples/
  example-memory.md        synthetic sample store
  README.md                sample audit run + what the flags mean
skills/
  control-theory-memory/   write-time rules (Hermes skill format)
  memory-hygiene/          cleanup-time rules (Hermes skill format)
```

The two `skills/` files are in Hermes skill format; the rules themselves are agent-agnostic — port them to whatever rule file your framework injects every turn.

## Quick start

1. Find your two install points and follow your framework's recipe in [docs/porting.md](docs/porting.md) — Claude Code, Codex, Cursor, or generic.
2. Paste [templates/injected-rules.md](templates/injected-rules.md) into the layer your agent sees every turn. Rules that aren't injected aren't applied.
3. Copy the two store templates and set a character budget; check occupancy with `python3 scripts/memory-audit.py <your>/MEMORY.md` — sample run in [examples/](examples/README.md).
4. Wire the cleanup loop (nightly or weekly) — with the guardrails in [docs/operations.md](docs/operations.md), not without — and log what it deletes for the first month.

## Status & claim ceiling

This is **n = 1 field notes**, not a controlled study:

- written from one long-running personal assistant's experience (months of daily use)
- the "60–70% density" figure is *observed practice*, not a measured law
- the failure incident is reported as it happened, not as an experiment
- treat the numbers as *starting points to tune*, not defaults to trust

## Sources

- H. S. Tsien, *Engineering Cybernetics*, McGraw-Hill, 1954.
- Donella H. Meadows, *Thinking in Systems: A Primer*, Chelsea Green, 2008.

Only concepts, chapter-level references and our own operational notes appear here. No text from either book is reproduced; please buy the books — they are both worth it.

## License

MIT — see [LICENSE](LICENSE).
