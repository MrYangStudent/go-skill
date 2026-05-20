"""
daily-digest-sender
通过 SMTP 以纯 HTML 邮件形式发送 GitHub 趋势日报。
支持 QQ 邮箱 / 163 / Gmail / 企业邮箱等任意 SMTP 服务。

核心改造（v2）：
  - 所有内容均为结构化 HTML，不再走 Markdown 中间态
  - CSS 全内联 + table 布局，兼容主流邮件客户端
  - 图表图片 CID 嵌入
  - AI 关键词自动高亮
  - 移动端自适应
"""

import datetime
import os
import re
import smtplib
import textwrap
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from secrets import get_secret
from typing import Optional


# ── 环境变量 ──────────────────────────────────────────────
# SMTP_HOST      : SMTP 服务器地址，如 smtp.qq.com
# SMTP_PORT      : SMTP 端口，默认 465（SSL）
# SMTP_USER      : 发件人邮箱地址
# SMTP_PASS      : SMTP 授权密码（QQ邮箱用授权码）
# DIGEST_TO      : 收件人，多个用逗号分隔
# DIGEST_SUBJECT : 邮件主题前缀，默认 "GitHub 趋势简报"
# ─────────────────────────────────────────────────────────


# ── 颜色常量（暗色 GitHub 主题）───────────────────────────
_C = {
    "bg": "#0d1117",
    "card_bg": "#161b22",
    "card_border": "#30363d",
    "card_inner": "#0d1117",
    "divider": "#21262d",
    "text": "#c9d1d9",
    "text_dim": "#8b949e",
    "text_bright": "#e6edf3",
    "accent": "#58a6ff",
    "accent_dim": "#79c0ff",
    "green": "#3fb950",
    "orange": "#f0883e",
    "gold": "#d29922",
    "kw_orange": "#ffa657",
    "link_bg": "rgba(88,166,255,0.1)",
    "link_border": "rgba(88,166,255,0.2)",
}

# 关键词高亮规则
_HIGHLIGHT_KEYWORDS = {
    "AI", "机器学习", "深度学习", "大模型", "LLM", "GPT", "Claude",
    "Python", "Rust", "Go", "TypeScript", "JavaScript", "Shell",
    "Agent", "RAG", "微调", "推理", "部署", "DevOps", "Web3",
    "区块链", "前端", "后端", "API", "自动化", "框架", "工具链",
    "隐私", "安全", "开源", "云原生", "边缘计算", "数据", "可视化",
    "趋势", "增长", "下降", "新兴", "热门", "活跃", "关注",
    "开发者", "生态", "插件", "CLI", "GUI",
}


def _highlight_keywords(text: str) -> str:
    """在纯文本中自动加粗关键词（避免重复包裹已有标签）。"""
    for kw in sorted(_HIGHLIGHT_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(
            r'(?<![\w\-<])(' + re.escape(kw) + r')(?![\w\->])',
            flags=re.IGNORECASE,
        )
        text = pattern.sub(
            f'<span style="color:{_C["kw_orange"]};font-weight:600;">\\1</span>',
            text,
        )
    return text


def _summary_md_to_html(md_text: str) -> str:
    """
    将 LLM 产出的趋势简报 MD 转为结构化 HTML。
    这是唯一还需要 MD→HTML 转换的地方（因为 LLM 输出是 MD）。

    输出结构：
    - ## 整体概述 → <div class="card"><h2>📋 整体概述</h2>...<div class="ai-insight">...</div></div>
    - ## 重点项目 → <div class="card"><h2>🔥 重点项目</h2>...<div class="project-card">...</div></div>
    - ## 技术趋势 → <div class="card"><h2>📈 技术趋势</h2>...<div class="ai-insight">...</div></div>
    """
    lines = md_text.strip().split("\n")
    sections = []  # [(title, [content_lines])]
    current_title = ""
    current_lines = []

    for line in lines:
        # 检测 ## 标题作为分节
        h2_match = re.match(r"^##\s+(.+)$", line)
        if h2_match:
            if current_title:
                sections.append((current_title, current_lines))
            current_title = h2_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, current_lines))
    elif current_lines:
        # 无标题的前言
        sections.append(("", current_lines))

    # 图标映射
    _ICONS = {
        "整体概述": "📋",
        "重点项目": "🔥",
        "技术趋势": "📈",
    }

    html_parts = []

    for title, content_lines in sections:
        icon = _ICONS.get(title, "📌")
        content_text = "\n".join(content_lines).strip()
        if not content_text:
            continue

        # 判断内容类型：有编号列表的视为项目卡片区，否则视为洞察区
        has_numbered_items = bool(re.search(r"^\d+\.\s+\*\*", content_text, re.M))

        if has_numbered_items:
            # 项目卡片区 — 解析每个编号项
            cards = _parse_project_items(content_text)
            cards_html = "\n".join(cards)
            html_parts.append(
                f'<div style="background:{_C["card_bg"]};border:1px solid {_C["card_border"]};'
                f'border-radius:12px;padding:16px;margin-bottom:16px;">'
                f'<h2 style="font-size:15px;font-weight:600;color:{_C["accent"]};'
                f'margin:0 0 12px 0;padding-bottom:8px;border-bottom:1px solid {_C["divider"]};">'
                f'{icon} {title}</h2>'
                f'{cards_html}'
                f'</div>'
            )
        else:
            # 洞察区 — 段落式内容，关键词高亮
            paragraphs = re.split(r"\n\n+", content_text)
            p_htmls = []
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                # 简单 MD → HTML
                p = re.sub(r"\*\*(.+?)\*\*", f'<span style="color:{_C["text_bright"]};font-weight:600;">\\1</span>', p)
                p = re.sub(r"`(.+?)`", f'<code style="background:rgba(88,166,255,0.12);color:{_C["accent_dim"]};padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;">\\1</code>', p)
                # 处理 - 开头的列表项
                p = re.sub(r"^[-*]\s+(.+)$", lambda m: f'<span style="display:block;margin:4px 0 4px 12px;">• {m.group(1)}</span>', p, flags=re.M)
                p = _highlight_keywords(p)
                # 换行 → <br>
                p = p.replace("\n", "<br>")
                p_htmls.append(
                    f'<p style="margin:0 0 10px 0;line-height:1.8;color:{_C["text"]};">{p}</p>'
                )

            insight_html = "\n".join(p_htmls)
            html_parts.append(
                f'<div style="background:{_C["card_bg"]};border:1px solid {_C["card_border"]};'
                f'border-radius:12px;padding:16px;margin-bottom:16px;">'
                f'<h2 style="font-size:15px;font-weight:600;color:{_C["accent"]};'
                f'margin:0 0 12px 0;padding-bottom:8px;border-bottom:1px solid {_C["divider"]};">'
                f'{icon} {title}</h2>'
                f'<div style="background:linear-gradient(135deg,rgba(88,166,255,0.06),rgba(63,185,80,0.06));'
                f'border-left:3px solid {_C["accent"]};padding:14px 16px;'
                f'border-radius:0 8px 8px 0;line-height:1.8;">'
                f'{insight_html}'
                f'</div>'
                f'</div>'
            )

    # 如果没有检测到 ## 标题，把全部内容当洞察区
    if not html_parts and md_text.strip():
        p = md_text.strip()
        p = re.sub(r"\*\*(.+?)\*\*", f'<span style="color:{_C["text_bright"]};font-weight:600;">\\1</span>', p)
        p = re.sub(r"`(.+?)`", f'<code style="background:rgba(88,166,255,0.12);color:{_C["accent_dim"]};padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;">\\1</code>', p)
        p = _highlight_keywords(p)
        p = p.replace("\n", "<br>")
        html_parts.append(
            f'<div style="background:{_C["card_bg"]};border:1px solid {_C["card_border"]};'
            f'border-radius:12px;padding:16px;margin-bottom:16px;">'
            f'<div style="background:linear-gradient(135deg,rgba(88,166,255,0.06),rgba(63,185,80,0.06));'
            f'border-left:3px solid {_C["accent"]};padding:14px 16px;'
            f'border-radius:0 8px 8px 0;line-height:1.8;">'
            f'<p style="margin:0;line-height:1.8;color:{_C["text"]};">{p}</p>'
            f'</div></div>'
        )

    return "\n".join(html_parts)


def _parse_project_items(content_text: str) -> list[str]:
    """解析编号列表中的项目条目，生成 project-card HTML。"""
    cards = []
    # 按 "数字. **" 分割
    items = re.split(r"(?=\n\d+\.\s+\*\*)", content_text)

    for item in items:
        item = item.strip()
        if not item:
            continue
        # 去掉开头编号
        item = re.sub(r"^\d+\.\s+", "", item)

        # 提取项目名 **xxx**
        name_match = re.match(r"\*\*(.+?)\*\*(.*)", item, re.S)
        if not name_match:
            # 非项目格式，当作普通文本
            item_html = re.sub(r"\*\*(.+?)\*\*", f'<span style="color:{_C["text_bright"]};font-weight:600;">\\1</span>', item)
            item_html = re.sub(r"`(.+?)`", f'<code style="background:rgba(88,166,255,0.12);color:{_C["accent_dim"]};padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;">\\1</code>', item_html)
            item_html = _highlight_keywords(item_html)
            item_html = item_html.replace("\n", "<br>")
            cards.append(
                f'<div style="background:{_C["card_inner"]};border-radius:8px;'
                f'padding:12px 14px;margin-bottom:10px;border-left:3px solid {_C["green"]};">'
                f'<p style="margin:0;line-height:1.6;font-size:13px;color:{_C["text"]};">{item_html}</p>'
                f'</div>'
            )
            continue

        name = name_match.group(1)
        rest = name_match.group(2).strip()

        # 提取 [语言] 标签
        lang_match = re.search(r"\[(\w+)\]", rest)
        lang_html = ""
        if lang_match:
            lang = lang_match.group(1)
            lang_html = f' <code style="background:rgba(88,166,255,0.12);color:{_C["accent_dim"]};padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;">{lang}</code>'

        # 提取星级
        stars_match = re.search(r"\+([\d,]+)\s*★", rest)
        stars_html = ""
        if stars_match:
            stars_html = f' <span style="color:{_C["gold"]};font-weight:600;font-size:13px;">+{stars_match.group(1)} ⭐</span>'

        # 剩余描述
        desc = rest
        if lang_match:
            desc = desc.replace(lang_match.group(0), "")
        if stars_match:
            desc = desc.replace(stars_match.group(0), "")
        desc = desc.strip().lstrip("—–:：").strip()

        # 描述中的 Markdown 转换
        desc = re.sub(r"\*\*(.+?)\*\*", f'<span style="color:{_C["text_bright"]};font-weight:600;">\\1</span>', desc)
        desc = re.sub(r"`(.+?)`", f'<code style="background:rgba(88,166,255,0.12);color:{_C["accent_dim"]};padding:2px 6px;border-radius:4px;font-size:90%;font-family:Consolas,monospace;">\\1</code>', desc)
        desc = _highlight_keywords(desc)
        desc = desc.replace("\n", "<br>")

        cards.append(
            f'<div style="background:{_C["card_inner"]};border-radius:8px;'
            f'padding:12px 14px;margin-bottom:10px;border-left:3px solid {_C["green"]};">'
            f'<div style="font-weight:600;color:{_C["text_bright"]};font-size:14px;margin-bottom:4px;">'
            f'{name}{lang_html}{stars_html}</div>'
            f'<div style="font-size:13px;color:{_C["text_dim"]};line-height:1.6;">{desc}</div>'
            f'</div>'
        )

    return cards


def _build_email_html(
    html_sections: list[str],
    image_paths: Optional[dict[str, str]] = None,
) -> str:
    """
    构建完整的邮件 HTML，暗色主题，全部内联样式。

    :param html_sections: 各模块输出的 HTML 片段列表
    :param image_paths: 图表图片路径，如 {"lang": "charts/lang.png", ...}
    :return: 完整 HTML 字符串
    """
    body_html = "\n".join(html_sections)

    # 生成图片区域
    chart_html = ""
    if image_paths:
        chart_items = []
        for name, path in image_paths.items():
            chart_items.append(
                f'<div style="margin-bottom:16px;text-align:center;">'
                f'<img src="cid:chart_{name}" alt="{name}" '
                f'style="max-width:100%;height:auto;border-radius:8px;border:1px solid {_C["card_border"]};">'
                f'</div>'
            )
        if chart_items:
            chart_html = (
                f'<div style="background:{_C["card_bg"]};border:1px solid {_C["card_border"]};'
                f'border-radius:12px;padding:16px;margin-bottom:16px;">'
                f'<h2 style="font-size:15px;font-weight:600;color:{_C["accent"]};'
                f'margin:0 0 12px 0;padding-bottom:8px;border-bottom:1px solid {_C["divider"]};">'
                f'📊 数据可视化</h2>'
                + "\n".join(chart_items)
                + '</div>'
            )

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    html = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub 趋势日报</title>
    <style>
      /* 邮件客户端兼容的 CSS 类定义 */
      .card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:16px; margin-bottom:16px; }
      .card h2 { font-size:15px; font-weight:600; color:#58a6ff; margin:0 0 12px 0; padding-bottom:8px; border-bottom:1px solid #21262d; }
      .lang-list { list-style:none; margin:0; padding:0; }
      .lang-list li { display:table; width:100%; padding:6px 0; border-bottom:1px solid #21262d; }
      .lang-list li:last-child { border-bottom:none; }
      .lang-rank { display:inline-block; width:22px; height:22px; border-radius:50%; background:#21262d; color:#8b949e; font-size:11px; font-weight:600; text-align:center; line-height:22px; margin-right:8px; vertical-align:middle; }
      .lang-name { font-weight:600; color:#e6edf3; margin-right:8px; }
      .lang-count { color:#8b949e; font-size:13px; margin-right:8px; }
      .lang-stars { color:#d29922; font-weight:600; font-size:13px; }
      .domain-group { margin-bottom:12px; padding:10px 12px; background:#0d1117; border-radius:8px; }
      .domain-title { font-size:13px; font-weight:600; color:#79c0ff; margin-bottom:6px; }
      .domain-repos { line-height:2; }
      .repo-tag { display:inline-block; padding:3px 10px; background:rgba(88,166,255,0.1); border:1px solid rgba(88,166,255,0.2); border-radius:20px; font-size:12px; color:#58a6ff; font-family:Consolas,monospace; text-decoration:none; margin:2px 0; }
      .compare-item { padding:6px 0; border-bottom:1px solid #21262d; }
      .compare-item:last-child { border-bottom:none; }
      .compare-key { font-weight:600; color:#e6edf3; margin-right:8px; }
      .compare-val { color:#c9d1d9; }
      .ai-insight { background:linear-gradient(135deg,rgba(88,166,255,0.06),rgba(63,185,80,0.06)); border-left:3px solid #58a6ff; padding:14px 16px; border-radius:0 8px 8px 0; line-height:1.8; }
      .ai-insight p { margin:0 0 10px 0; }
      .ai-insight p:last-child { margin-bottom:0; }
      .project-card { background:#0d1117; border-radius:8px; padding:12px 14px; margin-bottom:10px; border-left:3px solid #3fb950; }
      .project-name { font-weight:600; color:#e6edf3; font-size:14px; margin-bottom:4px; }
      .project-desc { font-size:13px; color:#8b949e; line-height:1.6; }
      .spike-badge { display:inline-block; background:rgba(240,136,62,0.15); color:#f0883e; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
      .rank-badge { display:inline-block; background:rgba(88,166,255,0.12); color:#79c0ff; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
      strong.kw { color:#ffa657; }
      code { background:rgba(88,166,255,0.12); color:#79c0ff; padding:2px 6px; border-radius:4px; font-size:90%; font-family:Consolas,monospace; }
    </style>
    </head>
    <body style="margin:0;padding:0;background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;line-height:1.7;-webkit-font-smoothing:antialiased;">
    <div style="max-width:640px;margin:0 auto;padding:16px;">

      <div style="text-align:center;padding:24px 0 16px;border-bottom:1px solid #30363d;margin-bottom:20px;">
        <h1 style="font-size:20px;font-weight:700;margin:0 0 4px 0;
          background:linear-gradient(135deg,#58a6ff,#3fb950);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          GitHub 趋势日报
        </h1>
        <p style="font-size:12px;color:#8b949e;margin:0;">__NOW_STR__ · 自动生成</p>
      </div>

      __BODY_HTML__

      __CHART_HTML__

      <div style="text-align:center;padding:20px 0;margin-top:20px;border-top:1px solid #30363d;font-size:11px;color:#6e7681;">
        由 GitHub 趋势监控 Pipeline 自动生成 · 如需退订请直接回复
      </div>

    </div>
    </body>
    </html>
    """)

    html = html.replace("__BODY_HTML__", body_html)
    html = html.replace("__CHART_HTML__", chart_html)
    html = html.replace("__NOW_STR__", now_str)
    return html


def _embed_images(
    msg: MIMEMultipart,
    image_paths: dict[str, str],
) -> None:
    """将图表图片以 CID 方式嵌入邮件。"""
    for name, path in image_paths.items():
        try:
            with open(path, "rb") as f:
                img_data = f.read()
            mime_img = MIMEImage(img_data)
            mime_img.add_header("Content-ID", f"<chart_{name}>")
            mime_img.add_header("Content-Disposition", "inline", filename=f"{name}.png")
            msg.attach(mime_img)
        except Exception as exc:
            print(f"[sender] 嵌入图片 {name} 失败：{exc}")


def send_digest(
    html_sections: Optional[list[str]] = None,
    md_content: Optional[str] = None,
    subject: Optional[str] = None,
    to_addrs: Optional[list[str]] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_pass: Optional[str] = None,
    image_paths: Optional[dict[str, str]] = None,
) -> None:
    """
    发送 HTML 邮件。支持两种模式：

    1. HTML 模式（推荐）：传入 html_sections（各模块 to_html() 产出的 HTML 片段列表）
    2. 兼容模式：传入 md_content，自动走 _summary_md_to_html 转换

    两者可同时传入，html_sections 拼在前面，md 转换结果追加在后面。
    """
    host = smtp_host or os.environ.get("SMTP_HOST", "smtp.qq.com")
    port = smtp_port or int(os.environ.get("SMTP_PORT", "465"))
    user = smtp_user or os.environ.get("SMTP_USER", "")
    password = smtp_pass or get_secret("SMTP_PASS")
    subject_prefix = os.environ.get("DIGEST_SUBJECT", "GitHub 趋势简报")

    if not user:
        raise ValueError("未配置 SMTP_USER，请在 .env 中设置")

    recipients = to_addrs or [
        addr.strip()
        for addr in os.environ.get("DIGEST_TO", user).split(",")
        if addr.strip()
    ]
    if not recipients:
        raise ValueError("未配置收件人（DIGEST_TO 或 to_addrs 参数）")

    # 组装 HTML sections
    all_sections = list(html_sections) if html_sections else []

    # 兼容：md_content 转换后追加
    if md_content:
        all_sections.append(_summary_md_to_html(md_content))

    if not all_sections:
        raise ValueError("未提供任何邮件内容（html_sections 或 md_content）")

    final_subject = subject or subject_prefix
    html_body = _build_email_html(all_sections, image_paths=image_paths)

    # 纯文本 fallback
    plain_text = md_content or "请使用支持 HTML 的邮件客户端查看此邮件。"

    # 构建正确的 MIME 结构：
    #   related → alternative(plain + html) + images(CID)
    # alternative 告诉邮件客户端"选最合适的格式展示"，
    # 否则客户端可能直接展示第一个 plain 文本（Markdown 原文）。
    msg = MIMEMultipart("related")
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = final_subject

    # alternative 层：纯文本 + HTML 互为备选
    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt_part)

    # 嵌入图片（CID 引用，挂在 related 层）
    if image_paths:
        _embed_images(msg, image_paths)

    print(f"[sender] 正在发送邮件 → {recipients}（via {host}:{port}）")
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
    print("[sender] 邮件发送成功")


def send_from_file(
    md_path: str | Path,
    **kwargs,
) -> None:
    """从 .md 文件读取内容后发送邮件（兼容模式）。"""
    path = Path(md_path)
    content = path.read_text(encoding="utf-8")
    date_hint = path.stem.replace("report_", "").replace("_", " ")
    subject = kwargs.pop("subject", None) or f"GitHub 趋势简报 · {date_hint}"
    send_digest(md_content=content, subject=subject, **kwargs)


if __name__ == "__main__":
    import argparse, glob

    parser = argparse.ArgumentParser(description="发送趋势简报邮件")
    parser.add_argument("--input", required=True, help="简报 .md 文件路径（支持 glob）")
    parser.add_argument("--to", default="", help="收件人，逗号分隔（覆盖环境变量）")
    parser.add_argument("--subject", default="", help="邮件主题")
    args = parser.parse_args()

    files = sorted(glob.glob(args.input))
    if not files:
        print(f"[sender] 未找到文件：{args.input}")
        raise SystemExit(1)

    md_path = files[-1]
    print(f"[sender] 读取简报：{md_path}")
    to_list = [a.strip() for a in args.to.split(",") if a.strip()] or None
    send_from_file(md_path, to_addrs=to_list, subject=args.subject or None)
