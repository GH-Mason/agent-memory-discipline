Environment is macOS with Homebrew; Python work uses per-project virtualenvs; the default shell is zsh.
§
Web fetching is routed through the configured scrape backend — it is the only one set up. When a domain fails, verify the backend supports it before retrying.
§
Generated files are named `YYYY-MM-DD_<topic>.<ext>` with the creation date; never overwrite an existing dated file, create a new one.
§
Lesson learned: the file writer follows symlinks. When replacing a symlinked config, write to the resolved target explicitly, or the edit lands somewhere unexpected.
§
Tool quirk: the screenshot helper returns file paths, not images. Read the image in a separate step; do not assume the path is the content.
§
Standing request from the user: never send an email without showing the draft first, and never send on their behalf without an explicit go-ahead.
§
Long-form notes live under `notes/`. Memory keeps pointers only, e.g. "hardware cleanup details: notes/2026-03-hardware.md — read before advising on disk cleanup".
§
The user prefers conclusions first, then supporting detail; on mobile channels keep answers under a few lines and skip operational play-by-play.
§
Backup policy: the working tree is backed up daily to the external volume; restore instructions, retention window, exclude list, and the encryption step are documented in docs/backup.md. Read that file before touching backup configuration, and note that the encryption passphrase is stored separately in the team vault — losing it makes the backups unusable, so never rotate or delete that entry without confirming the restore path end to end first.
§
Model routing: bulk background jobs use the cheap model; interactive sessions use the primary model. Provider keys rotate automatically from the configured pool.
§
Tool quirk (second note): the screenshot helper returns file paths, not images; the path is not the content — read the image separately.
§
Recurring correction: the user does not want progress narration on long tasks — report at decision points (blocked, finished, needs input), not every step.
§
The user's timezone is the machine's local timezone; when a schedule is specified without one, interpret it as local, and state the interpretation when confirming.
