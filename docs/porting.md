# Porting the rules to your agent

The rules are framework-agnostic; only the **installation points** differ. There are always two:

1. **The injected layer** — whatever your agent reads *every turn* (system prompt, rules file loaded at session start). The five always-on rules go here.
2. **The memory store** — a file (or files) the agent can read and write. The *content* goes here.

Plus, if you automate cleanup:

3. **The cleanup procedure** — a file the maintenance job loads by name, holding thresholds, protect-list, and report format.

> The most common setup mistake is putting the *content* in the injected layer (wastes budget every turn), or the *rules* only in a file nobody loads (never applies).

---

## The always-on block

Copy [`templates/injected-rules.md`](../templates/injected-rules.md) into your injected layer, then point its last line at your actual paths. Keep it short — it is charged against the context every single turn.

---

## Recipes

### Claude Code

- **Injected layer:** `CLAUDE.md` — the project one, and/or `~/.claude/CLAUDE.md` for a global default. Paste the always-on block under a `## Long-term memory` heading.
- **Store:** if your version has the memory feature enabled, it keeps a memory directory under `~/.claude/projects/<project-slug>/memory/` — an index file injected each session plus one fact per file. Apply the write rules to that directory and keep `USER`-class facts in a file automation never writes.
  Otherwise, use plain files: `<project>/memory/MEMORY.md` + `<project>/memory/USER.md`, starting from the two templates.
- **Cleanup:** keep the procedure as a separate markdown file (e.g. `memory/cleanup.md`) and have the maintenance session load it. Never let the procedure live only in a cron/scheduled prompt.

### Codex

- **Injected layer:** `AGENTS.md` — global (`~/.codex/AGENTS.md`) plus per-repo `AGENTS.md`. Paste the always-on block there.
- **Store:** recent versions ship a native memory system; in our setup, writes land in a small ad-hoc notes directory that is aggregated into memory for the next session, and direct edits to the aggregate file are not supported. Treat the native store as the hot path, and keep a plain `MEMORY.md` for anything the native pipeline won't accept.
- **Note:** writes may not appear in the injected context until a following session — verify by asking a fresh session what it remembers, rather than assuming the write failed.

### Cursor

- **Injected layer:** project rules live in `.cursor/rules/*.mdc`; set `alwaysApply: true` on the memory-rules file so it is injected on every request instead of being retrieved on demand. User-level rules go in Settings → Rules.
- **Store:** no native long-term memory — plain files, e.g. `memory/MEMORY.md` + `memory/USER.md` in the workspace, with the templates as the starting point.
- **Cleanup:** a scheduled script (cron/launchd/Task Scheduler) that runs the audit; the procedure file is required for anything destructive.

### Generic agent (system prompt + a file store)

- Put the always-on block in the system prompt.
- Add a read-at-start / write-at-end convention if there is no auto-injection: *"At the start of a session, read `memory/MEMORY.md`. When something worth keeping happens, update it — replace, don't append."*
- **Warning:** without injection, the rules only apply when the model happens to read the file. A framework with no injection point needs a hook, not just a convention.

### Hermes

- **Skills:** drop `skills/control-theory-memory/` and `skills/memory-hygiene/` into `~/.hermes/skills/`. They load on demand; attach `memory-hygiene` to the scheduled cleanup job by name.
- **Injected layer:** the memory files at `~/.hermes/memories/MEMORY.md` and `USER.md` are injected automatically each turn; keep budgets in config (`memory_char_limit`, `user_char_limit`).
- **Cleanup:** `hermes cron` job (agent mode, not a bare script — the decisions need semantics) with the skill attached.

---

## Picking budgets

| Agent type | Working memory | User profile |
|---|---|---|
| Small injected budget (system prompt is tight) | 2,000–4,000 chars | 1,000–2,000 |
| Large budget | 4,000–8,000 | 2,000–3,000 |

Start at the small end. Grow only if the level is *consistently* pressed against the ceiling at target occupancy — and even then, prefer merging entries over enlarging the budget. See [operations.md](operations.md) §4.

## Wiring the scripts

`scripts/memory-audit.py` is a read-only reporter (pure stdlib, no dependencies):

```bash
python3 scripts/memory-audit.py ~/path/to/MEMORY.md --limit 4000
python3 scripts/memory-audit.py ~/path/to/MEMORY.md --protect-file protect-list.txt --quiet   # cron-safe
python3 scripts/memory-audit.py ~/path/to/MEMORY.md --json                                     # machine-readable
```

Keep the protect-list in one file (one pattern per line, `#` comments allowed) and point `--protect-file` at it — the list then has a single source instead of drifting across cron commands. Entries that must survive rewording can carry the in-entry tag `#protect`, which the audit always honours.

Two companions close the loop:

- `scripts/cleanup-preflight.py` — run it as the **first step of every cleanup job**. It fails loudly if the procedure file is missing/truncated or the job's skill attachment is empty (docs/failure-modes.md explains why this must be code, not documentation).
- `scripts/memory-verify.py` — snapshot before an edit, then verify after: declared removals gone, declared additions present, and *nothing else* changed. This automates step 6 of the write flow.

Use the audit as the *measurement* step. The decision step — what to merge, compress, or keep — stays with an LLM following [templates/cleanup-checklist.md](../templates/cleanup-checklist.md). A scoring script can rank entries; it cannot tell a load-bearing rule from a stale note, and that distinction is the whole game.
