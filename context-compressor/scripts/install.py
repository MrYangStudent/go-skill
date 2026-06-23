#!/usr/bin/env python3
"""
Context Compressor — Multi-platform installation script.

Generates hook configurations for CodeBuddy, Claude Code, and OpenAI Codex
so the context-compressor skill can intercept tool outputs and inject compressed
content on all three platforms.

Usage:
    python install.py                  # install for all detected platforms
    python install.py --codebuddy      # only CodeBuddy
    python install.py --claude         # only Claude Code
    python install.py --codex          # only OpenAI Codex
    python install.py --dry-run        # preview without writing
    python install.py --uninstall      # remove hook configs from all platforms

Platform config locations:
  - CodeBuddy:  ~/.codebuddy/settings.json  (global, applies to all projects)
  - Claude Code: ~/.claude/settings.json    (global) or .claude/settings.json (project)
  - Codex:       ~/.codex/hooks.json        (global) or .codex/hooks.json (project)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Skill script paths ────────────────────────────────────────────────────────

def _get_skill_root() -> Path:
    """Resolve the skill root directory (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def _get_script_path(script_name: str) -> str:
    """Return the absolute path to a script in the skill's scripts/ directory."""
    return str(_get_skill_root() / "scripts" / script_name)


def _python_cmd() -> str:
    """Return the python command to use in hook configs."""
    if sys.platform == "win32":
        return "py"
    return "python3"


def _windows_path(path: str) -> str:
    """Convert a path to Windows backslash format."""
    return path.replace("/", "\\")


# ── Hook event definitions ────────────────────────────────────────────────────

# Matcher patterns for tool monitoring.  CodeBuddy and Codex use pipe-separated
# tool names; Claude Code also supports regex (e.g. "Read|Grep|...").
_TOOL_MATCHER = (
    "read_file|search_content|search_file|read_lints|"
    "execute_command|Grep|Glob|Bash"
)

# Core hook events common to all three platforms.
_CORE_EVENTS: Dict[str, list] = {
    "SessionStart": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "",
                    "timeout": 5,
                }
            ],
        }
    ],
    "PreToolUse": [
        {
            "matcher": _TOOL_MATCHER,
            "hooks": [
                {
                    "type": "command",
                    "command": "",  # filled in per-platform
                    "timeout": 3,
                }
            ],
        }
    ],
    "PostToolUse": [
        {
            "matcher": _TOOL_MATCHER,
            "hooks": [
                {
                    "type": "command",
                    "command": "",  # filled in per-platform
                    "timeout": 5,
                }
            ],
        }
    ],
    "PreCompact": [
        {
            "matcher": "auto",
            "hooks": [
                {
                    "type": "command",
                    "command": "",  # filled in per-platform
                    "timeout": 3,
                }
            ],
        },
        {
            "matcher": "manual",
            "hooks": [
                {
                    "type": "command",
                    "command": "",  # filled in per-platform
                    "timeout": 3,
                }
            ],
        },
    ],
    "Stop": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "",  # filled in per-platform
                    "timeout": 5,
                }
            ],
        }
    ],
}


def _fill_commands(hooks_config: dict, hook_script: str) -> dict:
    """Fill in the command fields with the actual hook script path."""
    import copy
    config = copy.deepcopy(hooks_config)
    python = _python_cmd()
    for event_name, matcher_list in config.items():
        for entry in matcher_list:
            for h in entry["hooks"]:
                h["command"] = f"{python} {hook_script}"
    return config


# ── Platform-specific config generators ───────────────────────────────────────

def _generate_codebuddy() -> Tuple[Path, dict]:
    """Generate CodeBuddy settings.json hook config."""
    user_home = str(Path.home())
    config_path = Path(user_home) / ".codebuddy" / "settings.json"

    hooks_script = _get_script_path("hook_compress.py")
    daily_script = _get_script_path("daily_report.py")

    # Read existing config if present.
    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)

    # Build hooks config with filled commands.
    hooks = _fill_commands(
        _CORE_EVENTS,
        hooks_script,
    )

    # Add Notification event for daily report (CodeBuddy-only).
    hooks["Notification"] = [
        {
            "matcher": "daily_report",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {daily_script} --persist",
                    "timeout": 10,
                }
            ],
        }
    ]

    config["hooks"] = hooks

    return config_path, config


def _generate_claude() -> Tuple[Path, dict]:
    """Generate Claude Code settings.json hook config.

    Claude Code uses:
      - Global: ~/.claude/settings.json
      - Project: .claude/settings.json

    We install to the global config by default.
    """
    user_home = str(Path.home())
    config_path = Path(user_home) / ".claude" / "settings.json"

    hooks_script = _get_script_path("hook_compress.py")

    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)

    hooks = _fill_commands(_CORE_EVENTS, hooks_script)

    # Claude Code supports PostCompact as well.
    hooks["PostCompact"] = [
        {
            "matcher": "auto|manual",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {hooks_script}",
                    "timeout": 3,
                }
            ],
        }
    ]

    # Notification is also supported in Claude Code.
    daily_script = _get_script_path("daily_report.py")
    hooks["Notification"] = [
        {
            "matcher": "daily_report",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {daily_script} --persist",
                    "timeout": 10,
                }
            ],
        }
    ]

    config["hooks"] = hooks

    return config_path, config


def _generate_codex() -> Tuple[Path, dict]:
    """Generate Codex hooks.json config.

    Codex uses:
      - Global: ~/.codex/hooks.json
      - Project: .codex/hooks.json

    We install to the global config by default.

    Note: Codex does not support the Notification event, so daily_report
    is not included in the hook config.  The Stop handler in hook_compress.py
    already persists daily stats, and SessionStart reads them back.
    """
    user_home = str(Path.home())
    config_path = Path(user_home) / ".codex" / "hooks.json"

    hooks_script = _get_script_path("hook_compress.py")

    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)

    hooks = _fill_commands(_CORE_EVENTS, hooks_script)

    # On Windows, add commandWindows variants.
    if sys.platform == "win32":
        for event_name, matcher_list in hooks.items():
            for entry in matcher_list:
                for h in entry["hooks"]:
                    h["commandWindows"] = h["command"]

    # Codex supports PostCompact.
    hooks["PostCompact"] = [
        {
            "matcher": "auto|manual",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {hooks_script}",
                    "timeout": 3,
                }
            ],
        }
    ]

    config["hooks"] = hooks

    return config_path, config


# ── Platform detection ────────────────────────────────────────────────────────

def detect_platforms() -> List[str]:
    """Detect which AI coding platforms are installed on this machine.

    Checks for the existence of config directories.
    """
    detected: List[str] = []
    home = Path.home()

    # CodeBuddy — always present if we're running in it.
    if (home / ".codebuddy").is_dir():
        detected.append("codebuddy")

    # Claude Code.
    if (home / ".claude").is_dir():
        detected.append("claude")

    # OpenAI Codex.
    if (home / ".codex").is_dir():
        detected.append("codex")

    # If nothing detected, default to CodeBuddy (we're running inside it).
    if not detected:
        detected.append("codebuddy")

    return detected


# ── Install / Uninstall ───────────────────────────────────────────────────────

def install(platforms: List[str], dry_run: bool = False) -> None:
    """Install hook configs for the specified platforms."""
    generators = {
        "codebuddy": _generate_codebuddy,
        "claude": _generate_claude,
        "codex": _generate_codex,
    }

    for plat in platforms:
        gen = generators.get(plat)
        if gen is None:
            print(f"[SKIP] Unknown platform: {plat}")
            continue

        config_path, config = gen()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = json.dumps(config, indent=2, ensure_ascii=False)

        if dry_run:
            print(f"[DRY-RUN] Would write {plat} config to: {config_path}")
            print(f"[DRY-RUN] Content preview ({len(json_str)} chars):")
            print(json_str[:2000])
            if len(json_str) > 2000:
                print(f"... ({len(json_str) - 2000} more chars)")
            print()
        else:
            config_path.write_text(json_str, encoding="utf-8")
            print(f"[OK] {plat}: {config_path} ({len(json_str)} chars)")


def uninstall(platforms: List[str]) -> None:
    """Remove hook configs from the specified platforms."""
    config_paths = {
        "codebuddy": Path.home() / ".codebuddy" / "settings.json",
        "claude": Path.home() / ".claude" / "settings.json",
        "codex": Path.home() / ".codex" / "hooks.json",
    }

    for plat in platforms:
        path = config_paths.get(plat)
        if path is None:
            continue
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                if "hooks" in existing:
                    del existing["hooks"]
                    if existing:
                        path.write_text(
                            json.dumps(existing, indent=2, ensure_ascii=False),
                            encoding="utf-8",
                        )
                    else:
                        path.write_text("{}\n", encoding="utf-8")
                print(f"[OK] Removed hooks from {plat}: {path}")
            except (json.JSONDecodeError, OSError) as e:
                print(f"[WARN] Could not modify {plat} config: {e}")
        else:
            print(f"[SKIP] {plat} config not found: {path}")


# ── Validation ────────────────────────────────────────────────────────────────

def validate() -> List[str]:
    """Validate that the skill is properly installed.

    Returns a list of issues found (empty = all good).
    """
    issues: List[str] = []
    skill_root = _get_skill_root()

    # Check required scripts exist.
    required_scripts = ["compress.py", "hook_compress.py", "mcp_compress_server.py"]
    for s in required_scripts:
        if not (skill_root / "scripts" / s).is_file():
            issues.append(f"Missing script: scripts/{s}")

    # Check cache directory.
    cache_dir = skill_root / "cache"
    if not cache_dir.is_dir():
        issues.append(f"Missing cache directory: {cache_dir}")
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            issues[-1] += " (created)"
        except OSError as e:
            issues[-1] += f" (cannot create: {e})"

    # Verify Python version.
    vi = sys.version_info
    if vi < (3, 10):
        issues.append(
            f"Python {vi.major}.{vi.minor} is too old; 3.10+ required"
        )

    return issues


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install context-compressor hooks for AI coding platforms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--codebuddy", action="store_true",
        help="Install for CodeBuddy only",
    )
    parser.add_argument(
        "--claude", action="store_true",
        help="Install for Claude Code only",
    )
    parser.add_argument(
        "--codex", action="store_true",
        help="Install for OpenAI Codex only",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Install for all platforms (default: auto-detect)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--uninstall", action="store_true",
        help="Remove hook configs instead of installing",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Check that the skill is properly set up",
    )

    args = parser.parse_args()

    # Validate mode.
    if args.validate:
        issues = validate()
        if issues:
            print("Issues found:")
            for i in issues:
                print(f"  - {i}")
        else:
            print("[OK] Skill validation passed.")
        return

    # Determine platforms.
    if args.all:
        platforms = ["codebuddy", "claude", "codex"]
    elif args.codebuddy or args.claude or args.codex:
        platforms = []
        if args.codebuddy:
            platforms.append("codebuddy")
        if args.claude:
            platforms.append("claude")
        if args.codex:
            platforms.append("codex")
    else:
        platforms = detect_platforms()

    if args.uninstall:
        uninstall(platforms)
        return

    print(f"Installing context-compressor for: {', '.join(platforms)}")
    print(f"Skill root: {_get_skill_root()}")
    print()

    # Run validation first.
    issues = validate()
    if issues:
        print("[WARN] Pre-install issues:")
        for i in issues:
            print(f"  - {i}")
        print()

    install(platforms, dry_run=args.dry_run)

    if not args.dry_run:
        print()
        print("Done! Hook scripts are now active for the configured platforms.")
        print()
        print("Tips:")
        print("  - Restart your AI coding tool for changes to take effect.")
        print("  - Run `python install.py --validate` to check installation.")
        print("  - Run `python install.py --dry-run` to preview config without writing.")


if __name__ == "__main__":
    main()
