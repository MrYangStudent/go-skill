#!/usr/bin/env python3
"""sync_skills.py — 按项目语言自动启用/禁用对应的 Skills。

在项目根目录放置 `.codebuddy/project-language` (如 python / go / vue / go, vue / python, vue)，
运行本脚本即可自动调整用户级 skills 的启用状态。

原理: CodeBuddy SKILL.md 支持 `disable: true` YAML 字段
(参见 https://www.codebuddy.ai/docs/zh/ide/Features/Skills)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

# 用户级 skills 目录
USER_SKILLS_DIR = Path.home() / ".codebuddy" / "skills"

# === 语言 → 技能前缀映射 ===
LANG_PREFIX_MAP: dict[str, list[str]] = {
    "python": ["python-"],
    "go": ["go-"],
    "vue": ["vue-"],
}

# === 始终启用的语言无关技能 ===
ALWAYS_ENABLED: set[str] = {
    "context-compressor",
    "prompt-master",
    "wiki-knowledge-base",
    "project-rules-init",
    "skill-auditor",
    "自己.skill",
    "skill-sync-manager",
}

# === 无语言前缀但实际是语言专用的技能 ===
# key=技能名, value=所属语言
LANGLESS_SKILLS: dict[str, str] = {}


def _read_frontmatter(skill_md: Path) -> tuple[str, str, str]:
    """读取 SKILL.md 的 frontmatter 前后部分。

    只匹配前两个 --- 分隔符，避免 markdown 内容中的 --- 干扰。

    Returns:
        (before_fm, fm_content, after_fm)
    """
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return ("", "", content)

    # 找到第一个 --- 后的换行符位置
    first_nl = content.index("\n", 3)
    before = content[: first_nl + 1]

    # 找到下一个 \n--- (第二个 --- 分隔符)
    rest = content[first_nl + 1 :]
    try:
        close_pos = rest.index("\n---")
    except ValueError:
        return ("", "", content)

    fm = rest[:close_pos]
    after = rest[close_pos:]
    return (before, fm, after)


def _has_disable(fm: str, raw_content: str = "") -> bool:
    """检查是否已有 disable 字段。兼容有/无 frontmatter 的技能。"""
    if fm:
        return bool(re.search(r"^disable:\s*true", fm, re.MULTILINE))
    return bool(re.search(r"^disable:\s*true", raw_content, re.MULTILINE))


def _disable_skill_file(skill_md: Path) -> bool:
    """确保 SKILL.md 被禁用。支持有/无 YAML frontmatter 的情况。

    Returns:
        True 如果实际修改了文件。
    """
    content = skill_md.read_text(encoding="utf-8")
    if re.search(r"^disable:\s*true", content, re.MULTILINE):
        return False  # 已禁用

    before, fm, after = _read_frontmatter(skill_md)
    if before:
        # 有 frontmatter → 在现有 frontmatter 中追加
        new_fm = fm.rstrip("\n") + "\ndisable: true"
        skill_md.write_text(f"{before}{new_fm}{after}", encoding="utf-8")
    else:
        # 无 frontmatter → 创建新的 frontmatter 包裹
        skill_md.write_text(f"---\ndisable: true\n---\n{content}", encoding="utf-8")
    return True


def _enable_skill_file(skill_md: Path) -> bool:
    """确保 SKILL.md 被启用（移除 disable 字段）。

    Returns:
        True 如果实际修改了文件。
    """
    before, fm, after = _read_frontmatter(skill_md)
    if not before:
        return False  # 无 frontmatter，无需处理

    if not re.search(r"^disable:\s*true", fm, re.MULTILINE):
        return False  # 没有 disable 字段

    new_fm = re.sub(r"\ndisable:\s*(true|false)\s*", "", fm).strip()

    if not new_fm:
        # frontmatter 仅包含 disable → 移除整个 frontmatter
        # after 以 "\n---\n" 开头，跳过这 5 个字符
        skill_md.write_text(after[5:], encoding="utf-8")
    else:
        skill_md.write_text(f"{before}{new_fm}{after}", encoding="utf-8")
    return True


SUPPORTED_LANGS = frozenset({"python", "go", "vue"})


def detect_languages(project_root: Path) -> list[str]:
    """从 .codebuddy/project-language 或项目文件检测项目语言。返回列表以支持多语言项目。"""
    lang_file = project_root / ".codebuddy" / "project-language"
    if lang_file.exists():
        raw = lang_file.read_text(encoding="utf-8").strip().lower()
        # 支持逗号分隔、空格分隔、多行
        candidates = raw.replace("\n", ",").replace(" ", ",").split(",")
        langs = [l.strip() for l in candidates if l.strip()]
        valid = [l for l in langs if l in SUPPORTED_LANGS]
        if valid:
            return valid

    # 回退：检测项目文件（可能多个）
    detected: list[str] = []
    if (project_root / "go.mod").exists():
        detected.append("go")
    if (project_root / "pyproject.toml").exists() or (
        project_root / "requirements.txt"
    ).exists():
        detected.append("python")

    return detected if detected else ["unknown"]


def get_skill_language(skill_name: str) -> Optional[str]:
    """根据技能名判断所属语言。"""
    # 检查语言前缀
    for lang, prefixes in LANG_PREFIX_MAP.items():
        for prefix in prefixes:
            if skill_name.startswith(prefix):
                return lang
    # 检查无前缀专用技能
    if skill_name in LANGLESS_SKILLS:
        return LANGLESS_SKILLS[skill_name]
    return None  # 语言无关


def sync_skills(
    project_root: Path,
    langs: list[str],
    dry_run: bool = False,
    quiet: bool = False,
) -> dict:
    """根据项目语言同步 skills 状态。

    Args:
        project_root: 项目根目录
        langs: 目标语言列表 (如 ["python", "vue"])
        dry_run: 仅预览不实际修改
        quiet: 静默模式 (hook 调用用，无输出)

    Returns:
        {"enabled": [...], "disabled": [...], "skipped": [...]}
    """
    result: dict = {"enabled": [], "disabled": [], "skipped": []}

    if not USER_SKILLS_DIR.exists():
        if not quiet:
            print(f"  ⚠ 用户 skills 目录不存在: {USER_SKILLS_DIR}")
        return result

    for skill_dir in sorted(USER_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        skill_name = skill_dir.name
        skill_lang = get_skill_language(skill_name)

        # 始终启用的技能 → 跳过
        if skill_name in ALWAYS_ENABLED:
            continue

        # 语言无关技能 → 跳过
        if skill_lang is None:
            continue

        # 匹配任意项目语言 → 确保启用
        if skill_lang in langs:
            if not dry_run:
                changed = _enable_skill_file(skill_md)
            else:
                before, fm, _ = _read_frontmatter(skill_md)
                changed = _has_disable(fm) if before else False
            if changed:
                result["enabled"].append(skill_name)
            else:
                result["skipped"].append(skill_name)
            continue

        # 不匹配任何项目语言 → 禁用
        if not dry_run:
            changed = _disable_skill_file(skill_md)
        else:
            content = skill_md.read_text(encoding="utf-8")
            changed = not _has_disable("", content)
        if changed:
            result["disabled"].append(skill_name)
            if not quiet:
                print(f"  🔕 禁用 {skill_name}")
        else:
            result["skipped"].append(skill_name)

    return result


def status(project_root: Path) -> None:
    """显示当前 skills 启用/禁用状态。"""
    langs = detect_languages(project_root)
    print(f"项目语言: {', '.join(langs)}")
    print(f"{'技能名':<40} {'语言':<10} {'状态':<10}")
    print("-" * 60)

    for skill_dir in sorted(USER_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        name = skill_dir.name
        skill_lang = get_skill_language(name) or "通用"
        content = skill_md.read_text(encoding="utf-8")
        _, fm, _ = _read_frontmatter(skill_md)
        disabled = _has_disable(fm, content)
        status_str = "🔕 禁用" if disabled else "✅ 启用"

        if name in ALWAYS_ENABLED:
            status_str = "🔒 始终启用"

        print(f"  {name:<38} {skill_lang:<10} {status_str:<10}")


def main() -> None:
    import argparse

    # Windows GBK 兼容
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # type: ignore[union-attr]

    parser = argparse.ArgumentParser(
        description="按项目语言自动同步 CodeBuddy Skills 启用状态"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="sync",
        choices=["sync", "status", "enable-all"],
        help="sync=同步启用/禁用 | status=查看状态 | enable-all=启用全部",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不实际修改文件",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式，仅在有变更时输出一行摘要 (供 hook 使用)",
    )
    args = parser.parse_args()

    project_root = Path.cwd()

    if args.action == "enable-all":
        if not args.quiet:
            print("🔧 启用全部 skills...")
        result = sync_skills(project_root, ["python"], dry_run=args.dry_run, quiet=args.quiet)
        result2 = sync_skills(project_root, ["go"], dry_run=args.dry_run, quiet=args.quiet)
        if args.dry_run and not args.quiet:
            print("\n[Dry-run 模式，未实际修改]")
        return

    if args.action == "status":
        status(project_root)
        return

    # sync
    langs = detect_languages(project_root)
    if "unknown" in langs:
        if not args.quiet:
            print(
                "❌ 无法检测项目语言。请在 .codebuddy/project-language "
                "中写入 python / go / vue（支持逗号分隔多语言，如 go, vue）"
            )
        sys.exit(0 if args.quiet else 1)

    result = sync_skills(project_root, langs, dry_run=args.dry_run, quiet=args.quiet)

    has_changes = len(result["enabled"]) + len(result["disabled"]) > 0

    if args.dry_run:
        if not args.quiet:
            print("\n[Dry-run 模式，未实际修改]")
    elif has_changes:
        msg_parts = []
        if result["enabled"]:
            msg_parts.append(f"启用 {len(result['enabled'])}")
        if result["disabled"]:
            msg_parts.append(f"禁用 {len(result['disabled'])}")
            msg_parts.append(f"~{len(result['disabled']) * 200}t saved")
        if args.quiet:
            print(f"[skills-sync] langs={','.join(langs)} | " + " | ".join(msg_parts))
        else:
            print(f"\n✅ 完成: " + ", ".join(msg_parts) + f" (跳过 {len(result['skipped'])})")


if __name__ == "__main__":
    main()
