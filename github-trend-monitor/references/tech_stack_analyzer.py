"""
tech-stack-analyzer — 技术栈趋势分析
分析 GitHub Trending 数据中的语言、领域、框架分布，
识别技术趋势变化，生成结构化报告。

功能：
  1. 语言分布统计（占比、排名变化）
  2. 领域聚类（AI/DevOps/Web/区块链 等）
  3. 多快照对比（跨时间维度趋势）
  4. AI 增强分析（可选，调用 LLM 生成趋势解读）

用法：
  python tech_stack_analyzer.py                     # 分析最新快照
  python tech_stack_analyzer.py --compare            # 对比最近两期
  python tech_stack_analyzer.py --ai                 # AI 增强分析
  python tech_stack_analyzer.py --lang python         # 只分析 Python 项目
"""

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)


# ── 领域分类规则 ──────────────────────────────────────────
DOMAIN_RULES: dict[str, list[str]] = {
    "AI / 机器学习": [
        "ai", "ml", "llm", "gpt", "claude", "deepseek", "openai",
        "transformer", "diffusion", "neural", "model", "agent",
        "chatbot", "rag", "embedding", "token", "inference",
        "machine-learning", "deep-learning", "nlp", "computer-vision",
    ],
    "开发工具": [
        "cli", "ide", "editor", "lsp", "debug", "test", "lint",
        "build", "deploy", "ci/cd", "devops", "git", "docker",
        "kubernetes", "k8s", "terraform", "makefile",
    ],
    "Web / 前端": [
        "react", "vue", "angular", "svelte", "next", "nuxt",
        "tailwind", "css", "html", "frontend", "web", "browser",
        "spa", "ssr",
    ],
    "后端 / API": [
        "api", "rest", "graphql", "grpc", "server", "backend",
        "microservice", "database", "redis", "postgres", "mysql",
        "orm", "sql",
    ],
    "安全 / 隐私": [
        "security", "privacy", "encrypt", "crypto", "vpn",
        "firewall", "auth", "oauth", "pentest", "vulnerability",
    ],
    "区块链 / Web3": [
        "blockchain", "crypto", "defi", "nft", "web3", "solana",
        "ethereum", "smart-contract", "token",
    ],
    "系统 / 基础设施": [
        "os", "kernel", "runtime", "compiler", "interpreter",
        "virtualization", "container", "network", "protocol",
        "storage", "filesystem",
    ],
    "数据 / 可视化": [
        "data", "analytics", "visualization", "chart", "dashboard",
        "etl", "pipeline", "spark", "kafka", "stream",
    ],
}


@dataclass
class LanguageStat:
    """语言统计。"""
    language: str
    count: int           # 项目数
    total_stars_today: int
    avg_stars_today: float
    repos: list[str] = field(default_factory=list)


@dataclass
class DomainStat:
    """领域统计。"""
    domain: str
    count: int
    repos: list[str] = field(default_factory=list)


@dataclass
class TechStackReport:
    """技术栈趋势报告。"""
    generated_at: str = ""
    total_repos: int = 0
    language_stats: list[LanguageStat] = field(default_factory=list)
    domain_stats: list[DomainStat] = field(default_factory=list)
    previous_comparison: dict = field(default_factory=dict)  # 跨期对比
    ai_analysis: str = ""  # AI 增强分析

    def to_markdown(self) -> str:
        lines = [
            f"# 📊 技术栈趋势分析",
            f"",
            f"生成时间：{self.generated_at}",
            f"分析项目数：{self.total_repos}",
            f"",
        ]

        # 语言分布 — 精简表格，手机一屏可看
        lines.append("## 语言分布")
        lines.append("")
        for i, stat in enumerate(self.language_stats[:10], 1):
            lines.append(
                f"{i}. **{stat.language or '—'}** "
                f"{stat.count} 项目 · "
                f"+{stat.total_stars_today:,} ⭐"
            )
        lines.append("")

        # 领域分布 — 一个项目一行
        lines.append("## 领域分布")
        lines.append("")
        for stat in self.domain_stats:
            lines.append(f"### {stat.domain}（{stat.count} 个）")
            lines.append("")
            for repo in stat.repos:
                lines.append(f"- `{repo}`")
            lines.append("")

        # 跨期对比
        if self.previous_comparison:
            lines.append("## 跨期对比")
            lines.append("")
            for key, val in self.previous_comparison.items():
                lines.append(f"- **{key}**：{val}")
            lines.append("")

        # AI 分析 — 空着由后续处理高亮
        if self.ai_analysis:
            lines.append("## AI 趋势解读")
            lines.append("")
            lines.append(self.ai_analysis)
            lines.append("")

        return "\n".join(lines)

    # ── 内联样式常量（邮件客户端兼容，不依赖 <style> 块）──
    _s = {
        "card": f"background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;margin-bottom:16px;",
        "card_h2": f"font-size:15px;font-weight:600;color:#58a6ff;margin:0 0 12px 0;padding-bottom:8px;border-bottom:1px solid #21262d;",
        "lang_list": f"list-style:none;margin:0;padding:0;",
        "lang_item": f"display:table;width:100%;padding:6px 0;border-bottom:1px solid #21262d;",
        "lang_item_last": f"display:table;width:100%;padding:6px 0;",
        "lang_rank": f"display:inline-block;width:22px;height:22px;border-radius:50%;background:#21262d;color:#8b949e;font-size:11px;font-weight:600;text-align:center;line-height:22px;margin-right:8px;vertical-align:middle;",
        "lang_name": f"font-weight:600;color:#e6edf3;margin-right:8px;",
        "lang_count": f"color:#8b949e;font-size:13px;margin-right:8px;",
        "lang_stars": f"color:#d29922;font-weight:600;font-size:13px;",
        "domain_group": f"margin-bottom:12px;padding:10px 12px;background:#0d1117;border-radius:8px;",
        "domain_title": f"font-size:13px;font-weight:600;color:#79c0ff;margin-bottom:6px;",
        "domain_repos": f"line-height:2;",
        "repo_tag": f"display:inline-block;padding:3px 10px;background:rgba(88,166,255,0.1);border:1px solid rgba(88,166,255,0.2);border-radius:20px;font-size:12px;color:#58a6ff;font-family:Consolas,monospace;text-decoration:none;margin:2px 0;",
        "compare_item": f"padding:6px 0;border-bottom:1px solid #21262d;",
        "compare_item_last": f"padding:6px 0;",
        "compare_key": f"font-weight:600;color:#e6edf3;margin-right:8px;",
        "compare_val": f"color:#c9d1d9;",
        "ai_insight": f"background:linear-gradient(135deg,rgba(88,166,255,0.06),rgba(63,185,80,0.06));border-left:3px solid #58a6ff;padding:14px 16px;border-radius:0 8px 8px 0;line-height:1.8;",
        "ai_p": f"margin:0 0 10px 0;color:#c9d1d9;",
        "kw": f"color:#ffa657;font-weight:600;",
    }

    def to_html(self) -> str:
        """
        生成结构化 HTML（邮件专用），全部内联样式 + CSS 类双重保障。
        邮件客户端常剥离 <style> 块，内联样式是唯一可靠方案。
        """
        s = self._s
        parts = []

        # ── 语言分布卡片 ──
        lang_items = []
        for i, stat in enumerate(self.language_stats[:10], 1):
            lang_name = stat.language or "—"
            is_last = (i == len(self.language_stats[:10]))
            lang_items.append(
                f'<li style="{s["lang_item_last"] if is_last else s["lang_item"]}">'
                f'<span class="lang-rank" style="{s["lang_rank"]}">{i}</span>'
                f'<span class="lang-name" style="{s["lang_name"]}">{lang_name}</span>'
                f'<span class="lang-count" style="{s["lang_count"]}">{stat.count} 项目</span>'
                f'<span class="lang-stars" style="{s["lang_stars"]}">+{stat.total_stars_today:,} ⭐</span>'
                '</li>'
            )
        if lang_items:
            parts.append(
                f'<div class="card" style="{s["card"]}">'
                f'<h2 style="{s["card_h2"]}">💻 语言分布</h2>'
                f'<ul class="lang-list" style="{s["lang_list"]}">'
                + "\n".join(lang_items)
                + '</ul>'
                '</div>'
            )

        # ── 领域分布卡片 ──
        domain_items = []
        for stat in self.domain_stats:
            repo_tags = []
            for repo in stat.repos:
                repo_tags.append(
                    f'<a href="https://github.com/{repo}" class="repo-tag" style="{s["repo_tag"]}">{repo}</a>'
                )
            domain_items.append(
                f'<div class="domain-group" style="{s["domain_group"]}">'
                f'<div class="domain-title" style="{s["domain_title"]}">{stat.domain}（{stat.count} 个）</div>'
                f'<div class="domain-repos" style="{s["domain_repos"]}">'
                + " ".join(repo_tags)
                + '</div>'
                '</div>'
            )
        if domain_items:
            parts.append(
                f'<div class="card" style="{s["card"]}">'
                f'<h2 style="{s["card_h2"]}">🏗️ 领域分布</h2>'
                + "\n".join(domain_items)
                + '</div>'
            )

        # ── 跨期对比卡片 ──
        if self.previous_comparison:
            cmp_items = []
            total = len(self.previous_comparison)
            for idx, (key, val) in enumerate(self.previous_comparison.items()):
                is_last = (idx == total - 1)
                cmp_items.append(
                    f'<div class="compare-item" style="{s["compare_item_last"] if is_last else s["compare_item"]}">'
                    f'<span class="compare-key" style="{s["compare_key"]}">{key}</span>'
                    f'<span class="compare-val" style="{s["compare_val"]}">{val}</span>'
                    '</div>'
                )
            parts.append(
                f'<div class="card" style="{s["card"]}">'
                f'<h2 style="{s["card_h2"]}">📈 跨期对比</h2>'
                + "\n".join(cmp_items)
                + '</div>'
            )

        # ── AI 趋势解读卡片 ──
        if self.ai_analysis:
            paragraphs = self.ai_analysis.split("\n\n") if "\n\n" in self.ai_analysis else [self.ai_analysis]
            ai_html_parts = []
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                p = _highlight_keywords_in_html(p)
                ai_html_parts.append(f'<p style="{s["ai_p"]}">{p}</p>')
            parts.append(
                f'<div class="card" style="{s["card"]}">'
                f'<h2 style="{s["card_h2"]}">🧠 AI 趋势解读</h2>'
                f'<div class="ai-insight" style="{s["ai_insight"]}">'
                + "\n".join(ai_html_parts)
                + '</div>'
                '</div>'
            )

        return "\n".join(parts)


# ── 关键词高亮（AI 趋势解读段落用） ──────────────────────
_HIGHLIGHT_KEYWORDS = {
    "AI", "机器学习", "深度学习", "大模型", "LLM", "GPT", "Claude",
    "Python", "Rust", "Go", "TypeScript", "JavaScript", "Shell",
    "Agent", "RAG", "微调", "推理", "部署", "DevOps", "Web3",
    "区块链", "前端", "后端", "API", "自动化", "框架", "工具链",
    "隐私", "安全", "开源", "云原生", "边缘计算", "数据", "可视化",
    "趋势", "增长", "下降", "新兴", "热门", "活跃", "关注",
    "开发者", "生态", "插件", "CLI", "GUI",
}


def _highlight_keywords_in_html(text: str) -> str:
    """在纯文本中自动加粗关键词（内联样式 + CSS 类双重保障）。"""
    for kw in sorted(_HIGHLIGHT_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(
            r'(?<![\w\-<])(' + re.escape(kw) + r')(?![\w\->])',
            flags=re.IGNORECASE,
        )
        text = pattern.sub(r'<strong class="kw" style="color:#ffa657;font-weight:600;">\1</strong>', text)
    return text


def _classify_domain(name: str, description: str, language: str) -> list[str]:
    """根据仓库名、描述、语言推断所属领域。"""
    text = f"{name} {description} {language}".lower()
    matched = []
    for domain, keywords in DOMAIN_RULES.items():
        if any(kw in text for kw in keywords):
            matched.append(domain)
    return matched or ["其他"]


def analyze_snapshot(
    repos: list[dict],
    lang_filter: str = "",
) -> TechStackReport:
    """
    分析单个快照的技术栈分布。

    :param repos: 项目数据列表
    :param lang_filter: 语言过滤
    :return: TechStackReport
    """
    # 语言过滤
    if lang_filter:
        repos = [r for r in repos if r.get("language", "").lower() == lang_filter.lower()]

    report = TechStackReport(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        total_repos=len(repos),
    )

    # ── 语言统计 ──
    lang_map: dict[str, LanguageStat] = {}
    for r in repos:
        lang = r.get("language") or "未标注"
        stars = r.get("stars_today", 0)
        name = r.get("name", "")
        if lang not in lang_map:
            lang_map[lang] = LanguageStat(
                language=lang, count=0, total_stars_today=0, avg_stars_today=0
            )
        lang_map[lang].count += 1
        lang_map[lang].total_stars_today += stars
        lang_map[lang].repos.append(name)

    for stat in lang_map.values():
        stat.avg_stars_today = stat.total_stars_today / stat.count if stat.count else 0

    report.language_stats = sorted(
        lang_map.values(), key=lambda s: s.total_stars_today, reverse=True
    )

    # ── 领域统计 ──
    domain_map: dict[str, DomainStat] = {}
    for r in repos:
        domains = _classify_domain(
            r.get("name", ""), r.get("description", ""), r.get("language", "")
        )
        for domain in domains:
            if domain not in domain_map:
                domain_map[domain] = DomainStat(domain=domain, count=0, repos=[])
            domain_map[domain].count += 1
            if r.get("name"):
                domain_map[domain].repos.append(r["name"])

    report.domain_stats = sorted(
        domain_map.values(), key=lambda s: s.count, reverse=True
    )

    return report


def compare_snapshots(
    current: list[dict],
    previous: list[dict],
) -> dict:
    """
    对比两个快照的变化趋势。

    :return: 对比摘要 dict
    """
    # 语言变化
    def _lang_counter(repos: list[dict]) -> Counter:
        return Counter(r.get("language") or "未标注" for r in repos)

    curr_langs = _lang_counter(current)
    prev_langs = _lang_counter(previous)

    comparison = {}

    # 新增语言
    new_langs = set(curr_langs.keys()) - set(prev_langs.keys())
    if new_langs:
        comparison["新增语言"] = ", ".join(sorted(new_langs))

    # 增长最快的语言
    lang_changes = {}
    for lang in set(curr_langs.keys()) & set(prev_langs.keys()):
        diff = curr_langs[lang] - prev_langs[lang]
        if diff != 0:
            lang_changes[lang] = diff

    if lang_changes:
        top_rising = sorted(lang_changes.items(), key=lambda x: x[1], reverse=True)[:3]
        top_falling = sorted(lang_changes.items(), key=lambda x: x[1])[:3]
        if top_rising:
            comparison["增长最快语言"] = ", ".join(
                f"{lang}({diff:+d})" for lang, diff in top_rising
            )
        if top_falling:
            comparison["下降最多语言"] = ", ".join(
                f"{lang}({diff:+d})" for lang, diff in top_falling
            )

    # 项目进出
    curr_names = {r.get("name") for r in current}
    prev_names = {r.get("name") for r in previous}
    newcomers = curr_names - prev_names
    dropouts = prev_names - curr_names
    if newcomers:
        comparison[f"新上榜项目"] = f"{len(newcomers)} 个"
    if dropouts:
        comparison[f"落榜项目"] = f"{len(dropouts)} 个"

    return comparison


def _load_json_snapshots(data_dir: str = "data") -> list[tuple[str, list[dict]]]:
    """加载所有快照，按时间排序。"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return []
    snapshots = []
    for f in sorted(data_path.glob("trending_*.json")):
        try:
            items = json.loads(f.read_text(encoding="utf-8"))
            snapshots.append((f.name, items))
        except (json.JSONDecodeError, OSError):
            continue
    return snapshots


def run_analysis(
    data_dir: str = "data",
    lang_filter: str = "",
    compare: bool = False,
    ai_enhanced: bool = False,
    no_send: bool = False,
    to_addrs: list[str] | None = None,
) -> TechStackReport:
    """
    执行技术栈分析。

    :return: TechStackReport
    """
    print("\n[analyzer] 技术栈趋势分析")
    snapshots = _load_json_snapshots(data_dir)

    if not snapshots:
        print("[analyzer] 无数据可分析")
        return TechStackReport()

    # 分析最新快照
    _, latest = snapshots[-1]
    report = analyze_snapshot(latest, lang_filter=lang_filter)

    # 跨期对比
    if compare and len(snapshots) >= 2:
        _, previous = snapshots[-2]
        report.previous_comparison = compare_snapshots(latest, previous)
        print(f"[analyzer] 已对比最近 2 期数据")

    # AI 增强分析
    if ai_enhanced:
        try:
            from secrets import get_secret
            from summarizer import summarize
            # 构造简化的数据给 AI
            summary_data = []
            for r in latest[:20]:
                summary_data.append({
                    "rank": r.get("rank", 0),
                    "name": r.get("name", ""),
                    "language": r.get("language", ""),
                    "stars_today": r.get("stars_today", 0),
                    "description": r.get("description", ""),
                })
            # 复用 summarizer 的 LLM 调用
            from openai import OpenAI
            api_key = get_secret("OPENAI_API_KEY")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.environ.get("SUMMARIZER_MODEL", "gpt-4o-mini")
            client = OpenAI(api_key=api_key, base_url=base_url)

            lang_summary = "\n".join(
                f"- {s.language}: {s.count} 项目, +{s.total_stars_today:,} 星"
                for s in report.language_stats[:10]
            )
            domain_summary = "\n".join(
                f"- {s.domain}: {s.count} 项目"
                for s in report.domain_stats
            )

            prompt = (
                "你是技术趋势分析师。以下是今日 GitHub Trending 的技术栈分析数据：\n\n"
                f"## 语言分布\n{lang_summary}\n\n"
                f"## 领域分布\n{domain_summary}\n\n"
                "请用 3-5 句话解读：1）当前最活跃的技术方向 2）可能的新兴趋势 3）开发者应关注什么。"
                "直接输出文字，无需标题。"
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=400,
            )
            report.ai_analysis = resp.choices[0].message.content.strip()
            print("[analyzer] AI 趋势解读已生成")
        except Exception as exc:
            print(f"[analyzer] AI 分析失败：{exc}")

    # 保存报告
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"tech_stack_{ts}.md"
    report_path.write_text(report.to_markdown(), encoding="utf-8")
    print(f"[analyzer] 报告已保存 → {report_path}")

    # 发送邮件
    if not no_send:
        try:
            from sender import send_digest
            subject = f"📊 技术栈趋势分析 · {datetime.now().strftime('%Y-%m-%d')}"
            send_digest(report.to_markdown(), subject=subject, to_addrs=to_addrs)
        except Exception as exc:
            print(f"[analyzer] 邮件发送失败：{exc}")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="技术栈趋势分析")
    parser.add_argument("--data-dir", default="data", help="数据目录")
    parser.add_argument("--lang", default="", help="语言过滤")
    parser.add_argument("--compare", action="store_true", help="对比上期数据")
    parser.add_argument("--ai", action="store_true", help="AI 增强分析")
    parser.add_argument("--no-send", action="store_true", help="不发送邮件")
    parser.add_argument("--to", default="", help="收件人（逗号分隔）")
    args = parser.parse_args()

    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()] or None
    run_analysis(
        data_dir=args.data_dir,
        lang_filter=args.lang,
        compare=args.compare,
        ai_enhanced=args.ai,
        no_send=args.no_send,
        to_addrs=to_addrs,
    )
