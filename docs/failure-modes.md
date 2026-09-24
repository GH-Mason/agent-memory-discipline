# Failure modes — and the incident that wrote this half of the code

Anti-patterns we have actually committed, plus a postmortem of the one that changed our design.

## Anti-pattern catalogue

### A1. Append-as-correction

- **Looks like:** the user corrects a fact; the agent adds a new entry with the corrected value "so nothing is lost".
- **Actually is:** two contradictory entries, no rule about which wins. Future retrieval is a coin flip, and the *stale* copy is not marked as stale.
- **Fix:** replace (or remove). If historical context matters, the old value goes to a note file, not to memory.

### A2. Budget enlargement

- **Looks like:** memory is full; raise the character limit.
- **Actually is:** symptom treatment. The full memory is full of noise; enlarging it preserves the noise and dilutes recall across all entries.
- **Fix:** compress to the target band; if compression is impossible, the entry set is too fine-grained — merge, don't expand.

### A3. Copy-as-redundancy

- **Looks like:** "this rule also exists in the documentation, so removing it from memory is safe."
- **Actually is:** confusion between two different *roles*. The doc is for humans/on-demand reading; the injected entry is what the agent sees every turn. A copy in a doc does not cover the injected role.
- **Fix:** the injected layer is only compressible, not eliminable, while the rule remains load-bearing. (Directly implicated in the incident below.)

### A4. Heuristic cleanup

- **Looks like:** a script scores entries by age / pattern ("contains dates", "mentions debugging") and proposes deletions.
- **Actually is:** freshness is not importance. User directives look stale and unimportant; historical trivia looks current.
- **Fix:** LLM-driven cleanup with a written procedure, a protect-list, and "flag for review" as the default under uncertainty.

### A5. Chatty maintenance

- **Looks like:** the audit reports every run ("no changes needed today").
- **Actually is:** trains the user to ignore the channel. The one run that matters arrives in a stream of noise.
- **Fix:** silent when clean; report only when something was done or needs review.

### A6. Storing the process, not just the fact

- **Looks like:** "how do I do X" workflows captured into long-term memory.
- **Actually is:** procedures expire with tool changes; facts about the user don't. Procedures belong in skill/doc files, loaded on demand.
- **Fix:** procedures → files; memory gets a pointer at most.

---

## Incident: the cleanup that deleted the rules protecting it

*Sanitised postmortem. Names, dates and paths removed; the mechanism is reproduced exactly.*

### Timeline

1. A nightly memory-cleanup job was running under an attached **procedure skill** that defined: threshold ~75% → target ~65%, scope = working memory only (never the user profile), an explicit protect-list, and "conservative by default."
2. At some point the job's configuration **lost its skill attachment** — the skills field was empty. Nothing failed loudly; the job kept firing nightly.
3. Without the procedure, the job improvised from a prompt that had itself drifted: it now applied a much harsher threshold (~90% → ~75%), ran a scoring script, and — the critical step — **accepted "a copy exists in the skill" as a reason to delete an entry from memory**.
4. That night it deleted three recent user directives from the injected layer, including one that was **explicitly on the protect-list** the job could no longer see.
5. Detected by the user, who noticed a rule they had stated two days earlier was gone.

### What actually went wrong

- **The guardrail was in the wrong place.** The protect-list lived in the skill. The job could run without the skill. A guardrail that can be silently detached is not a guardrail — it is documentation.
- **Drift had a channel.** Because the job prompt restated threshold numbers (instead of deferring to the procedure), a stale prompt could override the procedure. Duplicated configuration drifts.
- **The failure was silent.** Nothing failed; every run reported "ok". The only signal was user memory — the most expensive detector possible.
- **Plausible reasoning produced the worst outcome.** "The content still exists in the skill" is locally reasonable and globally wrong: it deletes from the *injected* layer while keeping the *on-demand* layer, which is the one combination that changes behaviour for the worse.

### Fixes applied

1. **Reattach + fail-safe:** the job must run with its procedure skill; the updated design treats a missing skill as a stop condition, not a licence to improvise. Made executable in [`scripts/cleanup-preflight.py`](../scripts/cleanup-preflight.py): the job starts by proving its procedure exists, is intact, and (when a config is supplied) has a non-empty skill attachment — failure is loud and the run stops.
2. **Thresholds live in one place** ([operations.md](operations.md) §1–4); the job prompt no longer restates them. Every other document references the canonical values instead of copying them — this repo itself now follows that rule.
3. **The copy-as-redundancy justification is explicitly banned** in the procedure, with the reasoning written down (A3 above) — because the counter-argument sounds plausible every time it comes up.
4. **A protect-list that is re-read each run**, plus "flag for review" as the default action under uncertainty. The list is fed to the audit from a single file (`--protect-file`), and entries that must survive rewording carry an in-entry `#protect` tag.
5. **The audit is not silent about itself:** every run writes a report to disk, and a snapshot of the store is taken before any destructive run. The *delivery* stays silent when clean; the *record* never is.

### Lessons that generalise

- **A guardrail must be unavoidable-at-run-time, not documented-somewhere.** If the safe path needs a file that can go missing, make its absence loud.
- **Silent automation failures are found by their consequences** — by then the damage is user-visible. Every unattended mutation loop needs its own liveness signal.
- **Watch for locally-plausible, globally-wrong reasoning.** The most dangerous delete justifications are the ones that sound like good engineering ("it's redundant", "it's stale", "nothing was lost").
- **Asymmetric costs need asymmetric defaults.** A wrong delete is silent, expensive, and irreversible; a skipped delete costs nothing. Default to *not deleting* and escalate instead.
- **Test the guardrail, not just the code.** If you have never run the aggressive case against your protect-list, you don't know that it holds (see the drills in [operations.md](operations.md)).

### Meta-lesson

The five principles in the README made the system *good*. This incident is what made them *hard*: it showed that the failure state of a memory system is not "wrong content" but **silently missing content** — and that the only durable defence is structural (fail-safe attachment, single-source configuration, default-to-keep), never procedural goodwill.
