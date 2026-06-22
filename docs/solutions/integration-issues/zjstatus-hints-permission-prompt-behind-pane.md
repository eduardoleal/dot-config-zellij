---
title: zjstatus-hints permission prompt stuck behind a pane
date: 2026-06-22
category: integration-issues
module: zellij-plugins
problem_type: integration_issue
component: tooling
symptoms:
  - "Plugin permission prompt for zjstatus-hints.wasm renders as a floating pane behind other panes"
  - "Pressing y/n never reaches the prompt; it cannot be focused or accepted"
  - "The same permission prompt reappears on every new session"
root_cause: missing_permission
resolution_type: config_change
severity: medium
related_components:
  - zjstatus
  - zjstatus-hints
  - zellij-autolock
tags:
  - zellij
  - plugin-permissions
  - headless-plugin
  - status-bar
  - zjstatus-hints
  - permissions-kdl
---

# zjstatus-hints permission prompt stuck behind a pane

## Problem

Zellij re-prompted for `zjstatus-hints.wasm` plugin permissions on every session, but the prompt could never be accepted: the plugin is headless/status-bar and has no focusable pane, so the floating prompt rendered behind other panes and `y`/`n` keypresses never reached it.

## Symptoms

- A permission prompt — `Plugin /Users/.../plugins/zjstatus-hints.wasm asks permission to ...` — appeared as a floating/bordered pane (titled `(.) - zjstatus-hints`, showing `PIN [ ]`).
- The pane sat *behind* other panes and could not be brought to focus.
- `y`/`n` keypresses never reached it, so the grant could not be accepted.
- The prompt reappeared on every new session.

## What Didn't Work

- **Trying to focus or interact with the floating prompt pane directly.** This is the core trap: `zjstatus-hints` is loaded headless via `load_plugins {}` and its output is piped into the zjstatus status bar (`format_left "{pipe_zjstatus_hints}"` in `layouts/default.kdl`). It has no focusable pane, so there is no UI surface that can ever receive the keypress — the prompt is structurally unacceptable through the Zellij UI.
- **Running `strings` on `zjstatus-hints.wasm`** to discover the requested permission names. Failed because Zellij serializes permission types as protobuf discriminants (integer field tags), not plain ASCII identifiers, so `grep` over the binary found no usable `PermissionType::*` names.

## Solution

1. Find the exact permissions the plugin requests in the upstream source — `github.com/b0o/zjstatus-hints`, `src/main.rs`:

   ```rust
   request_permission(&[
       PermissionType::ReadApplicationState,
       PermissionType::MessageAndLaunchOtherPlugins,
   ]);
   ```

2. Back up the grant store first — a malformed KDL silently wipes **all** grants:

   ```bash
   cd ~/Library/Caches/org.Zellij-Contributors.Zellij/
   cp permissions.kdl permissions.kdl.bak
   ```

3. Add an entry to `permissions.kdl` keyed by the **absolute `.wasm` path** (no `file:` prefix):

   ```kdl
   "/Users/eduardoleal/.config/zellij/plugins/zjstatus-hints.wasm" {
       ReadApplicationState
       MessageAndLaunchOtherPlugins
   }
   ```

4. Re-read the file to confirm it is still valid KDL.

5. Apply the grant. Running Zellij servers cache permissions in memory and only re-read on a fresh session, so the edit takes effect for **new** sessions only — existing sessions keep the stale state until restarted. Verify by starting a fresh session from **outside** Zellij (`zellij`). The guaranteed option, run from outside any session:

   ```bash
   zellij delete-all-sessions --force   # destroys ALL sessions — never run from inside a session
   ```

## Why This Works

`permissions.kdl` (`~/Library/Caches/org.Zellij-Contributors.Zellij/permissions.kdl`) **is** the grant store — there is no config flag to auto-allow permissions. It held an entry only for `zellij-autolock.wasm` and none for `zjstatus-hints.wasm`, so Zellij re-prompted every session. Because headless/status-bar plugins have no focusable pane, that prompt could never be satisfied interactively, creating an unbreakable loop. Writing the grant directly bypasses the prompt entirely. A single entry keyed by the absolute path covers both the `load_plugins {}` instance and the status-bar-piped instance, since both reference the same wasm path. Servers cache grants in memory, so the fix only lands on a fresh session.

## Prevention

- For **any** headless (`load_plugins {}`) or status-bar plugin (e.g. `zjstatus`, `zjstatus-hints`), pre-grant its permissions in `permissions.kdl` directly instead of relying on the interactive prompt — those prompts are unacceptable through the UI.
- Always keep a `.bak` of `permissions.kdl` before editing; a malformed KDL silently resets all grants.
- Discover a plugin's required permissions from its source `request_permission(...)` call, not from `.wasm` strings (protobuf discriminants are not greppable).
- Key each entry by the absolute `.wasm` path with no `file:` prefix.
- After editing, run `zellij delete-all-sessions --force` from outside Zellij and restart so servers re-read the file.

## Related Issues

- The repo `CLAUDE.md` documents this trap generically under **Notes > Permissions**; this doc is the detailed, plugin-specific walkthrough.
