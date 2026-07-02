"""
trend-dashboard-builder — 趋势可视化仪表盘
基于 data/ 目录的历史 JSON 数据，生成可交互的 HTML 仪表盘。

功能：
  1. 语言分布饼图
  2. 星标趋势折线图（多快照时间线）
  3. 热门项目排行条形图
  4. 领域分布图
  5. 最新榜单详情表

无需外部 JS/CSS，所有资源内联，单文件可独立运行。

用法：
  python trend_dashboard_builder.py                    # 生成仪表盘
  python trend_dashboard_builder.py --output dashboard # 指定输出文件名
  python trend_dashboard_builder.py --lang python       # 只看 Python 项目
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)


def _load_all_snapshots(data_dir: str = "data", lang_filter: str = "") -> list[dict]:
    """加载所有快照，附带时间戳。"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return []

    snapshots = []
    for f in sorted(data_path.glob("trending_*.json")):
        try:
            items = json.loads(f.read_text(encoding="utf-8"))
            if lang_filter:
                items = [r for r in items if r.get("language", "").lower() == lang_filter.lower()]
            # 从文件名提取时间
            # trending_all_daily_20260520_133323.json → 2026-05-20 13:33
            ts_match = f.stem.split("_")
            if len(ts_match) >= 4:
                date_str = ts_match[-2]  # 20260520
                time_str = ts_match[-1]  # 133323
                try:
                    dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    label = dt.strftime("%m-%d %H:%M")
                except ValueError:
                    label = f.name
            else:
                label = f.name

            snapshots.append({
                "label": label,
                "filename": f.name,
                "data": items,
            })
        except (json.JSONDecodeError, OSError):
            continue

    return snapshots


def _build_chart_data(snapshots: list[dict]) -> dict:
    """构建图表所需的 JSON 数据。"""
    from collections import Counter

    # 最新快照数据
    latest = snapshots[-1]["data"] if snapshots else []

    # 1. 语言分布
    lang_counter = Counter(r.get("language") or "未标注" for r in latest)
    lang_distribution = [
        {"language": lang, "count": count}
        for lang, count in lang_counter.most_common(15)
    ]

    # 2. 热门项目排行
    top_repos = sorted(latest, key=lambda r: r.get("stars_today", 0), reverse=True)[:20]
    top_repos_chart = [
        {
            "name": r.get("name", ""),
            "stars_today": r.get("stars_today", 0),
            "stars_total": r.get("stars_total", 0),
            "language": r.get("language", ""),
        }
        for r in top_repos
    ]

    # 3. 时间线趋势（语言项目数变化）
    timeline_labels = [s["label"] for s in snapshots]
    # 收集所有语言
    all_langs = set()
    for s in snapshots:
        for r in s["data"]:
            lang = r.get("language") or "未标注"
            all_langs.add(lang)

    # 取 top 5 语言做时间线
    top5_langs = [item["language"] for item in lang_distribution[:5]]
    timeline_series = []
    for lang in top5_langs:
        counts = []
        for s in snapshots:
            count = sum(1 for r in s["data"] if (r.get("language") or "未标注") == lang)
            counts.append(count)
        timeline_series.append({"language": lang, "counts": counts})

    # 4. 领域分布（复用 tech_stack_analyzer 的规则）
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
            "security", "privacy", "encrypt", "crypto",
            "auth", "oauth",
        ],
        "系统 / 基础设施": [
            "os", "kernel", "runtime", "compiler",
            "container", "network", "protocol",
        ],
    }

    domain_counter = Counter()
    for r in latest:
        text = f"{r.get('name', '')} {r.get('description', '')} {r.get('language', '')}".lower()
        matched = False
        for domain, keywords in DOMAIN_RULES.items():
            if any(kw in text for kw in keywords):
                domain_counter[domain] += 1
                matched = True
                break
        if not matched:
            domain_counter["其他"] += 1

    domain_distribution = [
        {"domain": d, "count": c} for d, c in domain_counter.most_common()
    ]

    # 5. 项目详情表
    detail_table = [
        {
            "rank": r.get("rank", 0),
            "name": r.get("name", ""),
            "description": r.get("description", "")[:100],
            "language": r.get("language", ""),
            "stars_total": r.get("stars_total", 0),
            "stars_today": r.get("stars_today", 0),
            "forks": r.get("forks", 0),
            "url": r.get("url", ""),
        }
        for r in latest
    ]

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_repos": len(latest),
        "lang_distribution": lang_distribution,
        "top_repos": top_repos_chart,
        "timeline_labels": timeline_labels,
        "timeline_series": timeline_series,
        "domain_distribution": domain_distribution,
        "detail_table": detail_table,
    }


def build_dashboard(
    data_dir: str = "data",
    output: str = "dashboard.html",
    lang_filter: str = "",
) -> Path:
    """
    生成 HTML 仪表盘。

    :param data_dir: 数据目录
    :param output: 输出文件名
    :param lang_filter: 语言过滤
    :return: 输出文件路径
    """
    snapshots = _load_all_snapshots(data_dir, lang_filter=lang_filter)

    if not snapshots:
        print("[dashboard] 无数据可用")
        return Path("")

    chart_data = _build_chart_data(snapshots)

    # 导入 Chart.js CDN（单文件可独立运行）
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub 趋势仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root {{
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text2: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --orange: #d29922;
    --red: #f85149;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg); color: var(--text);
    padding: 24px; max-width: 1280px; margin: 0 auto;
  }}
  h1 {{
    font-size: 24px; margin-bottom: 4px;
    background: linear-gradient(135deg, var(--accent), var(--green));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .meta {{ color: var(--text2); font-size: 13px; margin-bottom: 24px; }}
  .grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 16px; margin-bottom: 24px;
  }}
  @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px;
  }}
  .card h2 {{
    font-size: 15px; color: var(--text2);
    margin-bottom: 16px; text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .card canvas {{ max-height: 320px; }}
  .full {{ grid-column: 1 / -1; }}
  table {{
    width: 100%; border-collapse: collapse;
    font-size: 13px;
  }}
  th {{
    text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text2); font-weight: 500;
    position: sticky; top: 0; background: var(--card);
  }}
  td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
  tr:hover {{ background: rgba(88,166,255,0.06); }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .lang-badge {{
    display: inline-block; padding: 2px 8px;
    border-radius: 12px; font-size: 11px;
    background: rgba(88,166,255,0.15); color: var(--accent);
  }}
  .stars {{ color: var(--orange); font-weight: 600; }}
  .scroll-table {{ max-height: 480px; overflow-y: auto; }}
</style>
</head>
<body>

<h1>GitHub 趋势仪表盘</h1>
<p class="meta">
  生成时间：{chart_data['generated_at']} ·
  项目数：{chart_data['total_repos']} ·
  数据快照：{len(snapshots)} 份
</p>

<div class="grid">
  <div class="card">
    <h2>🔵 语言分布</h2>
    <canvas id="langChart"></canvas>
  </div>
  <div class="card">
    <h2>🟢 领域分布</h2>
    <canvas id="domainChart"></canvas>
  </div>
  <div class="card">
    <h2>⭐ 今日新增星标 Top 15</h2>
    <canvas id="topChart"></canvas>
  </div>
  <div class="card">
    <h2>📈 语言趋势变化</h2>
    <canvas id="timelineChart"></canvas>
  </div>
  <div class="card full">
    <h2>📋 最新榜单详情</h2>
    <div class="scroll-table">
      <table>
        <thead>
          <tr>
            <th>#</th><th>项目</th><th>语言</th>
            <th>今日新增</th><th>总星标</th><th>Fork</th>
          </tr>
        </thead>
        <tbody id="detailBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
// 调色板
const PALETTE = [
  '#58a6ff','#3fb950','#d29922','#f85149','#bc8cff',
  '#39d353','#79c0ff','#ffa657','#ff7b72','#d2a8ff',
  '#56d4dd','#7ee787','#e3b341','#ffa198','#b392f0'
];

const data = {json.dumps(chart_data, ensure_ascii=False)};

// 语言分布饼图
new Chart(document.getElementById('langChart'), {{
  type: 'doughnut',
  data: {{
    labels: data.lang_distribution.map(d => d.language),
    datasets: [{{
      data: data.lang_distribution.map(d => d.count),
      backgroundColor: PALETTE,
      borderWidth: 0
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'right', labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// 领域分布饼图
new Chart(document.getElementById('domainChart'), {{
  type: 'doughnut',
  data: {{
    labels: data.domain_distribution.map(d => d.domain),
    datasets: [{{
      data: data.domain_distribution.map(d => d.count),
      backgroundColor: PALETTE,
      borderWidth: 0
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'right', labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Top 项目条形图
new Chart(document.getElementById('topChart'), {{
  type: 'bar',
  data: {{
    labels: data.top_repos.map(d => d.name.length > 20 ? d.name.slice(0,20)+'…' : d.name),
    datasets: [{{
      label: '今日新增星标',
      data: data.top_repos.map(d => d.stars_today),
      backgroundColor: '#58a6ff',
      borderRadius: 4
    }}]
  }},
  options: {{
    responsive: true,
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#8b949e' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e6edf3', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// 语言趋势时间线
new Chart(document.getElementById('timelineChart'), {{
  type: 'line',
  data: {{
    labels: data.timeline_labels,
    datasets: data.timeline_series.map((s, i) => ({{
      label: s.language,
      data: s.counts,
      borderColor: PALETTE[i],
      backgroundColor: PALETTE[i] + '20',
      fill: true,
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
    }}))
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }},
    scales: {{
      x: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#8b949e' }} }},
      y: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#8b949e' }}, beginAtZero: true }}
    }}
  }}
}});

// 详情表
const tbody = document.getElementById('detailBody');
data.detail_table.forEach(r => {{
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>${{r.rank}}</td>
    <td><a href="${{r.url}}" target="_blank">${{r.name}}</a><br>
        <small style="color:var(--text2)">${{r.description}}</small></td>
    <td><span class="lang-badge">${{r.language || '—'}}</span></td>
    <td class="stars">+${{r.stars_today.toLocaleString()}}</td>
    <td>${{r.stars_total.toLocaleString()}}</td>
    <td>${{r.forks.toLocaleString()}}</td>
  `;
  tbody.appendChild(tr);
}});
</script>
</body>
</html>"""

    out_path = Path(output)
    out_path.write_text(html, encoding="utf-8")
    print(f"[dashboard] 仪表盘已生成 → {out_path}")
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub 趋势仪表盘生成")
    parser.add_argument("--data-dir", default="data", help="数据目录")
    parser.add_argument("--output", default="dashboard.html", help="输出文件名")
    parser.add_argument("--lang", default="", help="语言过滤")
    args = parser.parse_args()

    build_dashboard(
        data_dir=args.data_dir,
        output=args.output,
        lang_filter=args.lang,
    )
