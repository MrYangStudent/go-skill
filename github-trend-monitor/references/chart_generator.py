"""
chart_generator.py — 图表图片生成模块
用 matplotlib 生成趋势图表 PNG，供邮件嵌入。

生成图表：
  1. 语言分布环形图
  2. 领域分布水平条形图
  3. 今日新增星标 Top 10 条形图

用法：
  from chart_generator import generate_charts
  paths = generate_charts(data_dir="data", output_dir="charts")
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # 无 GUI 后端，服务器/脚本环境必须
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 中文字体配置 ──────────────────────────────────────────
# Windows 自带微软雅黑，matplotlib 默认不识别中文
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "C:/Windows/Fonts/simsun.ttc",  # 宋体
]

def _setup_chinese_font():
    """尝试设置中文字体，找不到则用默认字体（英文正常，中文可能方块）。"""
    for fp in _FONT_CANDIDATES:
        if Path(fp).exists():
            fm.fontManager.addfont(fp)
            prop = fm.FontProperties(fname=fp)
            plt.rcParams["font.family"] = prop.get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False  # 负号不方块

_setup_chinese_font()

# ── 配色方案 ──────────────────────────────────────────────
PALETTE = [
    "#58a6ff", "#3fb950", "#d29922", "#f85149", "#bc8cff",
    "#39d353", "#79c0ff", "#ffa657", "#ff7b72", "#d2a8ff",
    "#56d4dd", "#7ee787", "#e3b341", "#ffa198", "#b392f0",
]
BG_COLOR = "#0d1117"
CARD_COLOR = "#161b22"
TEXT_COLOR = "#e6edf3"
TEXT2_COLOR = "#8b949e"
BORDER_COLOR = "#30363d"


def _load_latest_snapshot(data_dir: str = "data") -> list[dict]:
    """加载最新一份快照。"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return []
    snapshots = sorted(data_path.glob("trending_*.json"))
    if not snapshots:
        return []
    return json.loads(snapshots[-1].read_text(encoding="utf-8"))


def _plot_lang_donut(repos: list[dict], output_path: Path) -> Path:
    """语言分布环形图。"""
    lang_counter = Counter(r.get("language") or "未标注" for r in repos)
    top = lang_counter.most_common(8)
    others = sum(lang_counter.values()) - sum(c for _, c in top)

    labels = [l for l, _ in top]
    sizes = [c for _, c in top]
    if others > 0:
        labels.append("其他")
        sizes.append(others)

    fig, ax = plt.subplots(figsize=(5, 4), facecolor=BG_COLOR)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 5 else "",
        colors=PALETTE[:len(sizes)],
        startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor=BG_COLOR, linewidth=2),
        textprops=dict(color=TEXT_COLOR, fontsize=10),
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_color(TEXT2_COLOR)

    ax.set_facecolor(BG_COLOR)
    # 中心文字
    ax.text(0, 0, f"{len(repos)}\n项目", ha="center", va="center",
            fontsize=14, fontweight="bold", color=TEXT_COLOR)
    ax.set_title("语言分布", color=TEXT_COLOR, fontsize=13, pad=12)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _plot_domain_bar(repos: list[dict], output_path: Path) -> Path:
    """领域分布水平条形图。"""
    DOMAIN_RULES = {
        "AI / 机器学习": [
            "ai", "ml", "llm", "gpt", "claude", "deepseek", "agent",
            "transformer", "diffusion", "model", "chatbot", "rag",
            "machine-learning", "deep-learning", "nlp",
        ],
        "开发工具": [
            "cli", "ide", "editor", "debug", "test", "lint",
            "build", "deploy", "devops", "git", "docker",
        ],
        "Web / 前端": [
            "react", "vue", "angular", "svelte", "next",
            "tailwind", "css", "frontend", "web",
        ],
        "后端 / API": [
            "api", "rest", "graphql", "server", "backend",
            "database", "redis", "postgres",
        ],
        "安全 / 隐私": [
            "security", "privacy", "encrypt", "crypto", "auth",
        ],
        "区块链 / Web3": [
            "blockchain", "crypto", "defi", "nft", "web3", "solana",
        ],
        "系统 / 基础设施": [
            "os", "kernel", "runtime", "compiler",
            "container", "network", "protocol",
        ],
        "数据 / 可视化": [
            "data", "analytics", "visualization", "chart", "dashboard",
        ],
    }

    domain_counter = Counter()
    for r in repos:
        text = f"{r.get('name', '')} {r.get('description', '')} {r.get('language', '')}".lower()
        matched = False
        for domain, keywords in DOMAIN_RULES.items():
            if any(kw in text for kw in keywords):
                domain_counter[domain] += 1
                matched = True
                break
        if not matched:
            domain_counter["其他"] += 1

    items = domain_counter.most_common()
    if not items:
        return output_path

    labels = [d for d, _ in items][::-1]
    sizes = [c for _, c in items][::-1]
    colors = PALETTE[:len(items)][::-1]

    fig, ax = plt.subplots(figsize=(5, max(3, len(items) * 0.55)), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(labels, sizes, color=colors, height=0.6, edgecolor=BG_COLOR)
    ax.bar_label(bars, padding=4, color=TEXT2_COLOR, fontsize=9)

    ax.set_xlim(0, max(sizes) * 1.25)
    ax.set_title("领域分布", color=TEXT_COLOR, fontsize=13, pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(BORDER_COLOR)
    ax.spines["left"].set_color(BORDER_COLOR)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _plot_top_repos(repos: list[dict], output_path: Path) -> Path:
    """今日新增星标 Top 10 水平条形图。"""
    top = sorted(repos, key=lambda r: r.get("stars_today", 0), reverse=True)[:10]
    if not top:
        return output_path

    names = [r["name"].split("/")[-1] for r in top][::-1]  # 只取仓库名，短一点
    stars = [r.get("stars_today", 0) for r in top][::-1]
    colors = PALETTE[:len(top)][::-1]

    fig, ax = plt.subplots(figsize=(5.5, max(3.5, len(top) * 0.45)), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(names, stars, color=colors, height=0.6, edgecolor=BG_COLOR)
    ax.bar_label(bars, labels=[f"+{s:,}" for s in stars], padding=4,
                 color=TEXT2_COLOR, fontsize=9)

    ax.set_xlim(0, max(stars) * 1.3)
    ax.set_title("今日新增星标 Top 10", color=TEXT_COLOR, fontsize=13, pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(BORDER_COLOR)
    ax.spines["left"].set_color(BORDER_COLOR)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_charts(
    data_dir: str = "data",
    output_dir: str = "charts",
) -> dict[str, str]:
    """
    生成所有图表 PNG。

    :return: 图表名 → 文件路径 的映射
    """
    repos = _load_latest_snapshot(data_dir)
    if not repos:
        print("[charts] 无数据可用")
        return {}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = {}

    print("[charts] 生成语言分布图…")
    p1 = _plot_lang_donut(repos, out / "lang_distribution.png")
    result["lang"] = str(p1)

    print("[charts] 生成领域分布图…")
    p2 = _plot_domain_bar(repos, out / "domain_distribution.png")
    result["domain"] = str(p2)

    print("[charts] 生成 Top 项目图…")
    p3 = _plot_top_repos(repos, out / "top_repos.png")
    result["top_repos"] = str(p3)

    print(f"[charts] 3 张图表已生成 → {out}/")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成趋势图表")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-dir", default="charts")
    args = parser.parse_args()

    paths = generate_charts(args.data_dir, args.output_dir)
    for name, path in paths.items():
        print(f"  {name}: {path}")
