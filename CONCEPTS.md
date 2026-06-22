# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Plugins

### Headless plugin
A plugin loaded in the background when a session starts, rather than into a visible pane. It runs without a focusable pane, so it cannot receive interactive input — notably, it can never accept its own permission prompt through the UI, which is why its grants must be written ahead of time. See [[Status-bar plugin]], [[Plugin permission grant]].

### Status-bar plugin
A plugin whose output is rendered inside the status bar instead of in its own pane. Like a [[Headless plugin]], it has no focusable pane and cannot accept an interactive permission prompt, so its [[Plugin permission grant|grants]] must be pre-written.

### Plugin permission grant
A standing authorization for one plugin to use a specific capability (reading application state, running commands, messaging other plugins, and so on). Grants are the only way a plugin's requested capabilities are approved — there is no global auto-allow — and they persist in an OS-level permission cache outside this repo, keyed per plugin. A running server holds grants in memory and re-reads the cache only when a new session starts, so a grant added mid-session takes effect only after a restart. A [[Headless plugin]] or [[Status-bar plugin]] must have its grants written ahead of time, since it has no pane to accept the prompt.
