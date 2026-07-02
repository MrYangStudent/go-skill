#!/usr/bin/env python3
"""
Skill Sync Manager — Multi-platform installation script.

Registers SessionStart hooks for CodeBuddy, Claude Code, and OpenAI Codex
so skills are automatically synced to the current project's language on
every session start.

Usage:
    python install.py                  # install for all detected platforms
    python install.py --codebuddy      # only CodeBuddy
    python install.py --claude         # only Claude Code
    python install.py --codex          # only OpenAI Codex
    python install.py --dry-run        # preview without writing
    python install.py --uninstall      # remove hook configs from all platforms
    python install.py --validate       # check skill integrity

Platform config locations:
  - CodeBuddy:   ~/.codebuddy/settings.json  (global)
  - Claude Code: ~/.claude/settings.json     (global)
  - Codex:       ~/.codex/hooks.json         (global)
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


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


# ── Hook event definitions ────────────────────────────────────────────────────

def _generate_codebuddy() -> Tuple[Path, dict]:
    """Generate CodeBuddy settings.json hook config.

    Registers a SessionStart hook that runs sync_skills.py --quiet.
    """
    config_path = Path.home() / ".codebuddy" / "settings.json"

    sync_script = _get_script_path("sync_skills.py")

    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)

    # Build hooks config.
    hooks = existing.get("hooks", {})

    # Ensure SessionStart exists.
    session_start = hooks.get("SessionStart", [])

    # Check if our hook is already registered.
    hook_exists = False
    for entry in session_start:
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if sync_script in cmd or "sync_skills.py" in cmd:
                hook_exists = True
                break
        if hook_exists:
            break

    if not hook_exists:
        session_start_entry = {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {sync_script} sync --quiet",
                    "timeout": 3,
                }
            ],
        }
        session_start.append(session_start_entry)

    hooks["SessionStart"] = session_start
    config["hooks"] = hooks

    return config_path, config


def _generate_claude() -> Tuple[Path, dict]:
    """Generate Claude Code settings.json hook config."""
    config_path = Path.home() / ".claude" / "settings.json"

    sync_script = _get_script_path("sync_skills.py")

    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)
    hooks = existing.get("hooks", {})
    session_start = hooks.get("SessionStart", [])

    hook_exists = False
    for entry in session_start:
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if sync_script in cmd or "sync_skills.py" in cmd:
                hook_exists = True
                break
        if hook_exists:
            break

    if not hook_exists:
        session_start_entry = {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {sync_script} sync --quiet",
                    "timeout": 3,
                }
            ],
        }
        session_start.append(session_start_entry)

    hooks["SessionStart"] = session_start
    config["hooks"] = hooks

    return config_path, config


def _generate_codex() -> Tuple[Path, dict]:
    """Generate OpenAI Codex hooks.json config."""
    config_path = Path.home() / ".codex" / "hooks.json"

    sync_script = _get_script_path("sync_skills.py")

    existing: dict = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            pass

    config = copy.deepcopy(existing)
    hooks = existing.get("hooks", {})
    session_start = hooks.get("SessionStart", [])

    hook_exists = False
    for entry in session_start:
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            if sync_script in cmd or "sync_skills.py" in cmd:
                hook_exists = True
                break
        if hook_exists:
            break

    if not hook_exists:
        session_start_entry = {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{_python_cmd()} {sync_script} sync --quiet",
                    "timeout": 3,
                }
            ],
        }
        # Codex on Windows needs commandWindows variant.
        if sys.platform == "win32":
            session_start_entry["hooks"][0]["commandWindows"] = session_start_entry["hooks"][0]["command"]
        session_start.append(session_start_entry)

    hooks["SessionStart"] = session_start
    config["hooks"] = hooks

    return config_path, config


# ── Platform detection ────────────────────────────────────────────────────────

def detect_platforms() -> List[str]:
    """Detect which AI coding platforms are installed on this machine."""
    detected: List[str] = []
    home = Path.home()

    if (home / ".codebuddy").is_dir():
        detected.append("codebuddy")
    if (home / ".claude").is_dir():
        detected.append("claude")
    if (home / ".codex").is_dir():
        detected.append("codex")
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
            print(json_str[:1000])
            if len(json_str) > 1000:
                print(f"... ({len(json_str) - 1000} more chars)")
            print()
        else:
            config_path.write_text(json_str, encoding="utf-8")
            print(f"[OK] {plat}: {config_path} ({len(json_str)} chars)")


def uninstall(platforms: List[str]) -> None:
    """Remove skill-sync hook configs from the specified platforms."""
    config_paths = {
        "codebuddy": Path.home() / ".codebuddy" / "settings.json",
        "claude": Path.home() / ".claude" / "settings.json",
        "codex": Path.home() / ".codex" / "hooks.json",
    }

    sync_script = _get_script_path("sync_skills.py")

    for plat in platforms:
        path = config_paths.get(plat)
        if path is None:
            continue
        if not path.exists():
            print(f"[SKIP] {plat} config not found: {path}")
            continue

        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            hooks = existing.get("hooks", {})
            session_start = hooks.get("SessionStart", [])

            # Remove entries that reference our script.
            original_len = len(session_start)
            session_start = [
                entry
                for entry in session_start
                if not any(
                    "sync_skills.py" in h.get("command", "")
                    for h in entry.get("hooks", [])
                )
            ]

            if len(session_start) < original_len:
                hooks["SessionStart"] = session_start
                if not session_start:
                    del hooks["SessionStart"]
                if not hooks:
                    del existing["hooks"]
                else:
                    existing["hooks"] = hooks

                path.write_text(
                    json.dumps(existing, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"[OK] Removed skill-sync hook from {plat}: {path}")
            else:
                print(f"[SKIP] No skill-sync hook found in {plat}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Could not modify {plat} config: {e}")


# ── Validation ────────────────────────────────────────────────────────────────

def validate() -> List[str]:
    """Validate that the skill is properly installed.

    Returns a list of issues found (empty = all good).
    """
    issues: List[str] = []
    skill_root = _get_skill_root()

    # Check required scripts exist.
    required_scripts = ["sync_skills.py"]
    for s in required_scripts:
        if not (skill_root / "scripts" / s).is_file():
            issues.append(f"Missing script: scripts/{s}")

    # Check SKILL.md exists.
    if not (skill_root / "SKILL.md").is_file():
        issues.append("Missing SKILL.md")

    # Check manifest.json exists.
    if not (skill_root / "manifest.json").is_file():
        issues.append("Missing manifest.json")

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
    if vi < (3, 8):
        issues.append(
            f"Python {vi.major}.{vi.minor} is too old; 3.8+ required"
        )

    return issues


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install skill-sync-manager hooks for AI coding platforms.",
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

    print(f"Installing skill-sync-manager for: {', '.join(platforms)}")
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
        print("Done! Skills will auto-sync on every session start.")
        print()
        print("Tips:")
        print("  - Ensure .codebuddy/project-language exists in your project root.")
        print("  - Run `python install.py --validate` to check installation.")
        print("  - Run `py sync_skills.py status` to view current skill states.")
        print("  - Run `python install.py --dry-run` to preview config.")


if __name__ == "__main__":
    main()
