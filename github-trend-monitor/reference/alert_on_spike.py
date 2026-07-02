"""
alert-on-spike — 星标激增告警
对比最新数据与历史快照，检测星标增速异常的项目。
支持邮件告警和控制台输出。

检测逻辑：
  1. 从 data/ 目录加载最近两次快照
  2. 同名项目 stars_today 对比，增速超过阈值则告警
  3. 新上榜项目（上期不在榜）视为新星项目，单独告警
  4. 生成告警文本，可选发送邮件

用法：
  python alert_on_spike.py                        # 默认阈值 2.0 倍
  python alert_on_spike.py --threshold 3.0        # 增速 ≥ 3 倍才告警
  python alert_on_spike.py --no-send              # 只输出不发送
  python alert_on_spike.py --top 5                # 只看 Top5 告警
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)


@dataclass
class SpikeAlert:
    """一条激增告警。"""
    name: str
    language: str
    stars_today_current: int
    stars_today_previous: int
    ratio: float          # 增速倍数
    stars_total: int
    url: str
    description: str = ""


@dataclass
class NewcomerAlert:
    """新星上榜告警。"""
    name: str
    language: str
    stars_today: int
    stars_total: int
    rank: int
    url: str
    description: str = ""


@dataclass
class AlertReport:
    """完整告警报告。"""
    spike_alerts: list[SpikeAlert] = field(default_factory=list)
    newcomer_alerts: list[NewcomerAlert] = field(default_factory=list)
    generated_at: str = ""

    @property
    def has_alerts(self) -> bool:
        return bool(self.spike_alerts) or bool(self.newcomer_alerts)

    def to_markdown(self) -> str:
        lines = [
            f"# 🔥 GitHub Trending 激增告警",
            f"",
            f"生成时间：{self.generated_at}",
            f"",
        ]

        if self.spike_alerts:
            lines.append("## ⚡ 星标激增项目")
            lines.append("")
            for alert in self.spike_alerts:
                lines.append(
                    f"- **{alert.name}** [{alert.language}]  "
                    f"+{alert.stars_today_current:,} (上期 +{alert.stars_today_previous:,})  "
                    f"🚀 **{alert.ratio:.1f}x**  "
                    f"★{alert.stars_total:,}"
                )
                if alert.description:
                    lines.append(f"  > {alert.description}")
                lines.append(f"  🔗 {alert.url}")
            lines.append("")

        if self.newcomer_alerts:
            lines.append("## 🌟 新星上榜")
            lines.append("")
            for alert in self.newcomer_alerts:
                lines.append(
                    f"- **{alert.name}** [{alert.language}]  "
                    f"+{alert.stars_today:,}  ★{alert.stars_total:,}  "
                    f"排名 #{alert.rank}"
                )
                if alert.description:
                    lines.append(f"  > {alert.description}")
                lines.append(f"  🔗 {alert.url}")
            lines.append("")

        if not self.has_alerts:
            lines.append("暂无激增告警，一切平稳 📊")

        return "\n".join(lines)

    def to_html(self) -> str:
        """
        生成结构化 HTML（邮件专用），全部内联样式 + CSS 类双重保障。
        邮件客户端常剥离 <style> 块，内联样式是唯一可靠方案。
        """
        # ── 内联样式常量 ──
        _s = {
            "card": "background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;margin-bottom:16px;",
            "card_h2": "font-size:15px;font-weight:600;color:#58a6ff;margin:0 0 12px 0;padding-bottom:8px;border-bottom:1px solid #21262d;",
            "project_card": "background:#0d1117;border-radius:8px;padding:12px 14px;margin-bottom:10px;border-left:3px solid #3fb950;",
            "project_card_spike": "background:#0d1117;border-radius:8px;padding:12px 14px;margin-bottom:10px;border-left:3px solid #f0883e;",
            "project_name": "font-weight:600;color:#e6edf3;font-size:14px;margin-bottom:4px;",
            "project_desc": "font-size:13px;color:#8b949e;line-height:1.6;",
            "spike_badge": "display:inline-block;background:rgba(240,136,62,0.15);color:#f0883e;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;",
            "rank_badge": "display:inline-block;background:rgba(88,166,255,0.12);color:#79c0ff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;",
            "code": "background:rgba(88,166,255,0.12);color:#79c0ff;padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;",
        }

        parts = []

        # ── 星标激增 ──
        if self.spike_alerts:
            spike_items = []
            for a in self.spike_alerts:
                spike_items.append(
                    f'<div class="project-card" style="{_s["project_card_spike"]}">'
                    f'<div class="project-name" style="{_s["project_name"]}">'
                    f'<a href="{a.url}" style="color:#e6edf3;text-decoration:none;">{a.name}</a>'
                    f' <code style="{_s["code"]}">{a.language}</code>'
                    f' <span class="spike-badge" style="{_s["spike_badge"]}">🚀 {a.ratio:.1f}x</span>'
                    f'</div>'
                    f'<div class="project-desc" style="{_s["project_desc"]}">'
                    f'今日 +{a.stars_today_current:,} · 上期 +{a.stars_today_previous:,} · 总计 ★{a.stars_total:,}'
                    f'</div>'
                    + (f'<div class="project-desc" style="{_s["project_desc"]}margin-top:4px;">{a.description}</div>' if a.description else '')
                    + '</div>'
                )
            parts.append(
                f'<div class="card" style="{_s["card"]}">'
                f'<h2 style="{_s["card_h2"]}">⚡ 星标激增项目</h2>'
                + "\n".join(spike_items)
                + '</div>'
            )

        # ── 新星上榜 ──
        if self.newcomer_alerts:
            new_items = []
            for a in self.newcomer_alerts:
                new_items.append(
                    f'<div class="project-card" style="{_s["project_card"]}">'
                    f'<div class="project-name" style="{_s["project_name"]}">'
                    f'<a href="{a.url}" style="color:#e6edf3;text-decoration:none;">{a.name}</a>'
                    f' <code style="{_s["code"]}">{a.language}</code>'
                    f' <span class="rank-badge" style="{_s["rank_badge"]}">#{a.rank}</span>'
                    f'</div>'
                    f'<div class="project-desc" style="{_s["project_desc"]}">'
                    f'今日 +{a.stars_today:,} · 总计 ★{a.stars_total:,}'
                    f'</div>'
                    + (f'<div class="project-desc" style="{_s["project_desc"]}margin-top:4px;">{a.description}</div>' if a.description else '')
                    + '</div>'
                )
            parts.append(
                f'<div class="card" style="{_s["card"]}">'
                f'<h2 style="{_s["card_h2"]}">🌟 新星上榜</h2>'
                + "\n".join(new_items)
                + '</div>'
            )

        # ── 无告警 ──
        if not self.has_alerts:
            parts.append(
                f'<div class="card" style="{_s["card"]}">'
                f'<h2 style="{_s["card_h2"]}">📊 激增检测</h2>'
                f'<p style="text-align:center;color:#8b949e;padding:16px 0;">暂无激增告警，一切平稳 ✅</p>'
                f'</div>'
            )

        return "\n".join(parts)


def _load_json_snapshots(data_dir: str = "data") -> list[tuple[str, list[dict]]]:
    """加载 data/ 目录下所有 JSON 快照，按时间排序。"""
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


def detect_spikes(
    data_dir: str = "data",
    threshold: float = 2.0,
    top_n: int = 10,
    tag_filter: str = "",
) -> AlertReport:
    """
    检测星标激增。

    :param data_dir: 数据目录
    :param threshold: 增速倍数阈值（如 2.0 = 2 倍）
    :param top_n: 最多返回 N 条告警
    :param tag_filter: 只看特定标签的数据（如 "all_daily"）
    :return: AlertReport
    """
    snapshots = _load_json_snapshots(data_dir)

    # 过滤标签
    if tag_filter:
        snapshots = [(name, data) for name, data in snapshots if tag_filter in name]

    if len(snapshots) < 2:
        print("[alert] 历史快照不足 2 份，无法对比激增")
        return AlertReport(generated_at=datetime.now().isoformat(timespec="seconds"))

    # 取最近两份
    _, current_data = snapshots[-1]
    _, previous_data = snapshots[-2]

    # 构建上期索引
    prev_map = {item["name"]: item for item in previous_data}

    report = AlertReport(generated_at=datetime.now().isoformat(timespec="seconds"))

    # 检测激增
    for item in current_data:
        name = item["name"]
        stars_today = item.get("stars_today", 0)
        prev_item = prev_map.get(name)

        if prev_item:
            prev_stars = prev_item.get("stars_today", 0)
            if prev_stars > 0 and stars_today > prev_stars:
                ratio = stars_today / prev_stars
                if ratio >= threshold:
                    report.spike_alerts.append(SpikeAlert(
                        name=name,
                        language=item.get("language", ""),
                        stars_today_current=stars_today,
                        stars_today_previous=prev_stars,
                        ratio=ratio,
                        stars_total=item.get("stars_total", 0),
                        url=item.get("url", f"https://github.com/{name}"),
                        description=item.get("description", ""),
                    ))
        else:
            # 新上榜
            report.newcomer_alerts.append(NewcomerAlert(
                name=name,
                language=item.get("language", ""),
                stars_today=stars_today,
                stars_total=item.get("stars_total", 0),
                rank=item.get("rank", 0),
                url=item.get("url", f"https://github.com/{name}"),
                description=item.get("description", ""),
            ))

    # 按增速排序，取 Top N
    report.spike_alerts.sort(key=lambda a: a.ratio, reverse=True)
    report.spike_alerts = report.spike_alerts[:top_n]
    report.newcomer_alerts.sort(key=lambda a: a.stars_today, reverse=True)
    report.newcomer_alerts = report.newcomer_alerts[:top_n]

    return report


def run_alert(
    data_dir: str = "data",
    threshold: float = 2.0,
    top_n: int = 10,
    no_send: bool = False,
    to_addrs: list[str] | None = None,
) -> AlertReport:
    """
    执行激增检测 + 可选发送告警邮件。

    :return: AlertReport
    """
    print(f"\n[alert] 检测星标激增（阈值 ≥ {threshold}x）")
    report = detect_spikes(data_dir=data_dir, threshold=threshold, top_n=top_n)

    if report.has_alerts:
        print(f"[alert] 发现 {len(report.spike_alerts)} 个激增项目，"
              f"{len(report.newcomer_alerts)} 个新星项目")
    else:
        print("[alert] 无激增告警")

    # 保存告警报告
    alert_dir = Path("alerts")
    alert_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    alert_path = alert_dir / f"alert_{ts}.md"
    alert_path.write_text(report.to_markdown(), encoding="utf-8")
    print(f"[alert] 告警报告 → {alert_path}")

    # 发送邮件
    if report.has_alerts and not no_send:
        try:
            from sender import send_digest
            subject = f"🔥 GitHub Trending 激增告警 · {datetime.now().strftime('%Y-%m-%d')}"
            send_digest(report.to_markdown(), subject=subject, to_addrs=to_addrs)
        except Exception as exc:
            print(f"[alert] 告警邮件发送失败：{exc}")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Trending 星标激增告警")
    parser.add_argument("--data-dir", default="data", help="数据目录")
    parser.add_argument("--threshold", type=float, default=2.0, help="增速倍数阈值")
    parser.add_argument("--top", type=int, default=10, help="最多 N 条告警")
    parser.add_argument("--no-send", action="store_true", help="只输出不发送邮件")
    parser.add_argument("--to", default="", help="收件人（逗号分隔）")
    args = parser.parse_args()

    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()] or None
    run_alert(
        data_dir=args.data_dir,
        threshold=args.threshold,
        top_n=args.top,
        no_send=args.no_send,
        to_addrs=to_addrs,
    )
