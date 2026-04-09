#!/usr/bin/env python3
"""update-plugin-docs.py

PostToolUse hook (Bash) — fires after every Bash tool call.
If a .wasm file in plugins/ was modified in the last 90 seconds,
regenerates the active-plugin table in CLAUDE.md between the
<!-- PLUGINS:START --> and <!-- PLUGINS:END --> markers.

Registry: add an entry to KNOWN_PLUGINS whenever you install a new plugin.
Auto-detected: keybinding trigger, load_plugins membership, layout membership.
"""

import json
import re
import sys
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

PLUGINS_DIR = Path.home() / ".config/zellij/plugins"
CONFIG_KDL  = Path.home() / ".config/zellij/config.kdl"   # symlink → ~/Documents/config.kdl
LAYOUT_KDL  = Path.home() / ".config/zellij/layouts/default.kdl"
CLAUDE_MD   = Path.home() / ".config/zellij/CLAUDE.md"

RECENT_SECONDS = 90   # treat .wasm modified within this window as "just added"
MARKER_START   = "<!-- PLUGINS:START -->"
MARKER_END     = "<!-- PLUGINS:END -->"

# ── Plugin registry ───────────────────────────────────────────────────────────
# Keys are the exact .wasm filenames.
# trigger=None  → auto-detected from keybindings / load_plugins / layout.
# trigger=str   → hardcoded (e.g. "Layout (status bar)", "Headless (load_plugins)").

KNOWN_PLUGINS: dict[str, dict] = {
    "zjstatus.wasm": {
        "name":    "zjstatus",
        "purpose": "Customizable status bar — mode badges, session, tabs, datetime",
        "source":  "dj95/zjstatus",
        "version": "0.22.0",
        "trigger": "Layout (status bar)",
    },
    "zellij-autolock.wasm": {
        "name":    "zellij-autolock",
        "purpose": "Auto-locks Zellij when vim/nvim/hx/fzf/git/zoxide/atuin is focused",
        "source":  "fresh2dev/zellij-autolock",
        "version": "0.2.2",
        "trigger": "Headless (load_plugins)",
    },
    "room.wasm": {
        "name":    "room",
        "purpose": "Fuzzy type-to-filter tab switcher with quick-jump by number",
        "source":  "rvcas/room",
        "version": "1.2.1",
        "trigger": None,
    },
    "harpoon.wasm": {
        "name":    "harpoon",
        "purpose": "Bookmark and instantly jump to specific panes (`a` add, `d` remove, `Enter` jump)",
        "source":  "Nacho114/harpoon",
        "version": "0.3.0",
        "trigger": None,
    },
    "zellij_forgot.wasm": {
        "name":    "zellij-forgot",
        "purpose": "Floating keybinding cheatsheet — auto-reads bindings from config.kdl",
        "source":  "karimould/zellij-forgot",
        "version": "0.4.2",
        "trigger": None,
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_keybinding(wasm_name: str, config: str) -> str:
    """Return the key (e.g. 'Ctrl e') that launches this wasm via LaunchOrFocusPlugin."""
    pattern = rf'bind\s+"([^"]+)"\s*\{{[^{{}}]*?LaunchOrFocusPlugin[^{{}}]*?{re.escape(wasm_name)}'
    m = re.search(pattern, config, re.DOTALL)
    return m.group(1) if m else ""


def in_load_plugins(alias_or_path: str, config: str) -> bool:
    """Check if alias or path fragment appears inside the load_plugins block."""
    if not alias_or_path:
        return False
    m = re.search(r"load_plugins\s*\{([^}]+)\}", config, re.DOTALL)
    return bool(m and alias_or_path in m.group(1))


def in_layout(wasm_name: str, layout: str) -> bool:
    return wasm_name in layout


def is_active(wasm_name: str, info: dict, config: str, layout: str) -> bool:
    """Return True if the plugin is referenced anywhere in the active config."""
    if info.get("trigger"):
        return True   # hardcoded means intentionally active
    if find_keybinding(wasm_name, config):
        return True
    alias = info.get("name", "")
    if in_load_plugins(alias, config) or in_load_plugins(wasm_name, config):
        return True
    if in_layout(wasm_name, layout):
        return True
    return False


def resolve_trigger(wasm_name: str, info: dict, config: str, layout: str) -> str:
    if info.get("trigger"):
        return info["trigger"]
    kb = find_keybinding(wasm_name, config)
    if kb:
        return f"`{kb}`"
    alias = info.get("name", "")
    if in_load_plugins(alias, config) or in_load_plugins(wasm_name, config):
        return "Headless (load_plugins)"
    if in_layout(wasm_name, layout):
        return "Layout"
    return "—"


def source_link(source: str) -> str:
    if not source:
        return "—"
    return f"[{source}](https://github.com/{source})"


def build_table(wasm_files: list[Path], config: str, layout: str) -> str:
    header = "| Plugin | WASM | Trigger | Purpose | Source | Version |\n"
    sep    = "|--------|------|---------|---------|--------|---------|\n"
    rows   = []

    for wasm in sorted(wasm_files):
        name = wasm.name
        info = KNOWN_PLUGINS.get(name, {})

        if not is_active(name, info, config, layout):
            continue

        rows.append(
            f"| {info.get('name', name.replace('.wasm', ''))}"
            f" | `{name}`"
            f" | {resolve_trigger(name, info, config, layout)}"
            f" | {info.get('purpose', '_add description_')}"
            f" | {source_link(info.get('source', ''))}"
            f" | {info.get('version', '—')}"
            f" |\n"
        )

    return header + sep + "".join(rows)


def update_claude_md(table: str) -> None:
    text = CLAUDE_MD.read_text()
    new_block = f"{MARKER_START}\n{table}{MARKER_END}"
    new_text = re.sub(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        new_block,
        text,
        flags=re.DOTALL,
    )
    if new_text != text:
        CLAUDE_MD.write_text(new_text)
        print("[update-plugin-docs] Plugin table updated in CLAUDE.md")
    else:
        print("[update-plugin-docs] Plugin table unchanged")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Only run on Bash tool events
    try:
        event = json.loads(sys.stdin.read())
        if event.get("tool_name") != "Bash":
            return
    except Exception:
        return

    # Only run if a .wasm was recently modified
    wasm_files = list(PLUGINS_DIR.glob("*.wasm"))
    recently_changed = [f for f in wasm_files if time.time() - f.stat().st_mtime < RECENT_SECONDS]
    if not recently_changed:
        return

    config = CONFIG_KDL.read_text()
    layout = LAYOUT_KDL.read_text()
    table  = build_table(wasm_files, config, layout)
    update_claude_md(table)


if __name__ == "__main__":
    main()
