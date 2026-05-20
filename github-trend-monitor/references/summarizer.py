"""
ai-trend-summarizer
读取 tracker.py 输出的 JSON，调用 LLM 生成 Markdown 趋势简报。
支持 OpenAI / 任意兼容 OpenAI 协议的接口（通过环境变量配置）。
"""

import json
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── 环境变量 ─────────────────────────────────────────────
# OPENAI_API_KEY   : API 密钥（必填）
# OPENAI_BASE_URL  : 自定义接口地址，默认 https://api.openai.com/v1
# SUMMARIZER_MODEL : 模型名称，默认 gpt-4o-mini
# ─────────────────────────────────────────────────────────


from secrets import get_secret


def _get_client():
    """懒加载 OpenAI 客户端，便于在没有 openai 包时给出清晰报错。"""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "缺少 openai 包，请先执行：pip install openai"
        )
    api_key = get_secret("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def _build_prompt(repos: list[dict], since: str, top_n: int) -> str:
    """拼装发给 LLM 的 prompt。"""
    items = repos[:top_n]
    lines = []
    for r in items:
        lang = f"[{r['language']}]" if r["language"] else ""
        lines.append(
            f"#{r['rank']} {r['name']} {lang}\n"
            f"   描述：{r['description'] or '（无）'}\n"
            f"   ★总计 {r['stars_total']:,}  今日新增 +{r['stars_today']:,}  Fork {r['forks']:,}\n"
        )
    repo_block = "\n".join(lines)

    prompt = textwrap.dedent(f"""
        你是一位技术趋势分析师。以下是今天 GitHub Trending {since} 榜单前 {top_n} 名项目数据：

        {repo_block}

        请生成一份简洁的技术趋势简报，要求：
        1. 整体概述：用 2-3 句话归纳本期热点技术方向
        2. 重点项目：选出最值得关注的 3-5 个项目，各用 2-3 句话介绍亮点及值得关注的原因
        3. 技术趋势：识别 2-3 个可能的趋势信号（语言/框架/领域热点变化）
        4. 格式要求：使用 Markdown，标题层级不超过 ##，精炼，总字数不超过 600 字

        直接输出 Markdown 内容，无需前后寒暄。
    """).strip()
    return prompt


def summarize(
    repos: list[dict],
    since: str = "daily",
    top_n: int = 25,
    model: Optional[str] = None,
) -> str:
    """
    调用 LLM 生成趋势简报文本（Markdown 字符串）。

    :param repos: tracker.py 输出的仓库字典列表
    :param since: 时间范围标签，仅用于 prompt 描述
    :param top_n: 分析前 N 条
    :param model: 指定模型，优先于环境变量
    :return: Markdown 文本
    """
    client = _get_client()
    model = model or os.environ.get("SUMMARIZER_MODEL", "gpt-4o-mini")
    prompt = _build_prompt(repos, since, top_n)

    print(f"[summarizer] 正在调用模型 {model}，分析 {min(top_n, len(repos))} 个项目…")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200,
    )
    content = response.choices[0].message.content.strip()
    return content


def summarize_from_file(
    json_path: str | Path,
    since: str = "daily",
    top_n: int = 25,
    output_dir: str = "reports",
    model: Optional[str] = None,
) -> Path:
    """
    从 JSON 文件读取数据，生成简报并保存 .md 文件。

    :return: 保存的 .md 文件路径
    """
    repos = json.loads(Path(json_path).read_text(encoding="utf-8"))
    content = summarize(repos, since=since, top_n=top_n, model=model)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = out / f"report_{since}_{ts}.md"

    header = (
        f"# GitHub 趋势简报 · {since.capitalize()} · "
        f"{datetime.now().strftime('%Y-%m-%d')}\n\n"
    )
    md_path.write_text(header + content, encoding="utf-8")
    print(f"[summarizer] 简报已保存 → {md_path}")
    return md_path


if __name__ == "__main__":
    import argparse, glob

    parser = argparse.ArgumentParser(description="AI 趋势分析")
    parser.add_argument("--input", required=True, help="tracker 输出的 JSON 文件路径（支持 glob）")
    parser.add_argument("--since", default="daily")
    parser.add_argument("--top", type=int, default=25, help="分析前 N 条")
    parser.add_argument("--output", default="reports")
    parser.add_argument("--model", default="", help="指定模型名")
    args = parser.parse_args()

    files = sorted(glob.glob(args.input))
    if not files:
        print(f"[summarizer] 未找到文件：{args.input}")
        raise SystemExit(1)

    json_path = files[-1]  # 取最新一个
    print(f"[summarizer] 读取数据：{json_path}")
    summarize_from_file(
        json_path,
        since=args.since,
        top_n=args.top,
        output_dir=args.output,
        model=args.model or None,
    )
