# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Plugins

### Headless plugin
A plugin loaded in the background when a session starts, rather than into a visible pane. It runs without a focusable pane, so it cannot receive interactive input — notably, it can never accept its own permission prompt through the UI, which is why its grants must be written ahead of time. See [[Status-bar plugin]], [[Plugin permission grant]].

### Status-bar plugin
A plugin whose output is rendered inside the status bar instead of in its own pane. Like a [[Headless plugin]], it has no focusable pane and cannot accept an interactive permission prompt, so its [[Plugin permission grant|grants]] must be pre-written.

### Plugin permission grant
A standing authorization for one plugin to use a specific capability (reading application state, running commands, messaging other plugins, and so on). Grants are the only way a plugin's requested capabilities are approved — there is no global auto-allow — and they persist in an OS-level permission cache outside this repo, keyed per plugin. A running server holds grants in memory and re-reads the cache only when a new session starts, so a grant added mid-session takes effect only after a restart. A [[Headless plugin]] or [[Status-bar plugin]] must have its grants written ahead of time, since it has no pane to accept the prompt.

## Tab Naming

### Pane title
The Zellij-exposed title for a pane. Codex/Claude-style CLIs can publish task context here, making it the primary MVP source for semantic tab names before any hook metadata or LLM compression is considered.

### Deterministic tab label
A generated tab name derived from local Zellij-visible context, usually project plus activity. It is the fallback label when no pushed task metadata is available or when the LLM label endpoint is unavailable.

### Pushed tab metadata
Task or session context sent into the tab namer by a tool integration such as a Claude hook, shell hook, or future agent hook. This is the only MVP input that may be sent to an LLM for label compression; visible pane text and scrollback stay outside the model boundary.

### Manual tab-name override
A user-provided tab name that automation must preserve. Once a tab is manually renamed, generated labels are ignored for that tab until the override is cleared or automation is explicitly re-enabled.

### Dual-mode installer
A `zellij-tab-namer` installer contract that supports the current CLI watcher setup and the native WASM plugin setup through one stable user-facing setup flow. CLI mode may be available before the WASM artifact exists, but WASM mode remains a first-class target rather than a later rewrite of the install experience.

### Activation flag
An explicit installer option that allows disruptive activation work, such as restarting or deleting Zellij sessions. Without an activation flag, installer setup may edit files and report that a fresh session is needed, but it must not kill active Zellij work.

### Installer backup
A restorable copy created before the installer changes Zellij config or permission-cache files. Backups are part of the installer safety contract, not an optional debug artifact.
