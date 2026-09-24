# MEMORY.template.md — starter working-memory file

> Copy into your agent's memory directory. Entries are separated by a line
> containing a single `§` (pick your own separator; keep it unambiguous and
> never let it occur inside an entry). One entry = one topic.
>
> Suggested budget: ~4,000 characters. Operate at 60–70% occupancy.

<!-- ── entry 1: environment fact ─────────────────────────────────────── -->
<One environment fact or convention. State it as a fact, not an instruction.
e.g. "Web fetching goes through <service>; it is the only backend configured.">
§
<!-- ── entry 2: a tool quirk + its workaround ────────────────────────── -->
<Tool quirks and their workarounds, one per entry. Include the *why* only if
the why changes how the workaround is applied.>
§
<!-- ── entry 3: a lesson with a structural cause ─────────────────────── -->
<Lessons with a root cause, not incident narration. "X fails when Y, because Z;
so do W" — not "on day N, X broke.">
§
<!-- ── entry 4: pointer to long-form storage ─────────────────────────── -->
<Weak-observability pointer. Long-form content lives in a file; memory keeps
a one-line pointer: "Details: <path>. Read when <condition>.">
§
<!-- ── entry 5: a standing convention ────────────────────────────────── -->
<Conventions the agent must honour every session. If it is genuinely
load-bearing, it also lives in your rule file (redundancy, principle 5).>

<!--
Maintenance notes — delete these when you start using the file, or keep
them in your procedure doc instead of the memory itself.

- Write flow: classify → route → dedupe → cost-test → commit (atomic) → verify.
- On correction: REPLACE. Never add a corrected twin.
- Never enlarge the budget to absorb growth; compress to target instead.
- Protect-list entries (never auto-deleted): <list them in your cleanup
  procedure, and re-read the list each run — not once, at setup time.>
-->
