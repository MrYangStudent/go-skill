"""
github-trending-tracker
抓取 GitHub Trending 日榜 / 周榜 / 月榜，返回结构化数据并保存 JSON。
依赖：requests, beautifulsoup4
"""

import json
import os
import re
import time
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com/trending"
# 备用：通过第三方 API 获取 trending（无需翻墙）
TRENDING_API = "https://api.gitterapp.com/repositories"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

SINCE_MAP = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
}


def _get_session() -> requests.Session:
    """创建带代理和 SSL 宽松配置的 Session（内网环境安全可接受）。"""
    session = requests.Session()
    session.headers.update(HEADERS)
    # 读取代理
    proxy = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        print(f"[tracker] 使用代理：{proxy}")
    # 内网代理环境 SSL 证书可能不被信任，关闭验证（仅影响本进程）
    session.verify = False
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    return session


@dataclass
class TrendingRepo:
    rank: int
    name: str           # owner/repo
    description: str
    language: str
    stars_total: int
    stars_today: int
    forks: int
    url: str
    fetched_at: str


def _parse_number(text: str) -> int:
    """把 '1,234' / '12.5k' 这类字符串转成 int。"""
    text = text.strip().replace(",", "")
    if not text:
        return 0
    match = re.match(r"([\d.]+)([kK]?)", text)
    if not match:
        return 0
    num = float(match.group(1))
    if match.group(2).lower() == "k":
        num *= 1000
    return int(num)


def _get_proxy() -> dict | None:
    """从环境变量读取代理配置。"""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if proxy:
        return {"https": proxy, "http": proxy}
    return None


def fetch_trending_api(
    language: str = "",
    since: str = "daily",
    session: requests.Session | None = None,
) -> list[TrendingRepo]:
    """
    通过第三方 API 获取 GitHub Trending（无需翻墙）。
    API 来源：https://github.com/nicehash/github-trending-api
    """
    s = session or _get_session()
    since = SINCE_MAP.get(since, "daily")
    params = {"since": since}
    if language:
        params["language"] = language

    print("[tracker] 尝试通过 API 获取 trending…")
    resp = s.get(TRENDING_API, params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json()
    now = datetime.now().isoformat(timespec="seconds")
    repos: list[TrendingRepo] = []

    for rank, item in enumerate(items, start=1):
        # API 返回字段名可能不同，做兼容
        name = item.get("author", "") + "/" + item.get("name", item.get("repo", ""))
        if not name or name == "/":
            name = item.get("fullName", item.get("full_name", f"unknown-{rank}"))
        repos.append(
            TrendingRepo(
                rank=rank,
                name=name,
                description=item.get("description", "") or "",
                language=item.get("language", item.get("programmingLanguage", "")) or "",
                stars_total=item.get("stars", item.get("currentPeriodStars", 0)) or 0,
                stars_today=item.get("currentPeriodStars", item.get("stars_since", 0)) or 0,
                forks=item.get("forks", 0) or 0,
                url=item.get("url", f"https://github.com/{name}"),
                fetched_at=now,
            )
        )
    return repos


def fetch_trending(
    language: str = "",
    since: str = "daily",
    retry: int = 3,
) -> list[TrendingRepo]:
    """
    抓取 GitHub Trending 页面。自动尝试两种方式：
    1. 直连/代理爬取 GitHub 页面
    2. 若失败，走第三方 API

    :param language: 语言过滤，如 'python'、'go'、'typescript'，空字符串表示不过滤
    :param since: 'daily' | 'weekly' | 'monthly'
    :param retry: 失败重试次数
    :return: TrendingRepo 列表
    """
    session = _get_session()
    since = SINCE_MAP.get(since, "daily")
    url = f"{BASE_URL}/{language}?since={since}" if language else f"{BASE_URL}?since={since}"

    # ── 方式 1：爬取 GitHub 页面 ──────────────────────
    resp = None
    for attempt in range(retry):
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            print(f"[tracker] 页面爬取第 {attempt + 1} 次失败：{exc}")
            if attempt < retry - 1:
                time.sleep(2 ** attempt)
            else:
                print("[tracker] 页面爬取不可用，切换到 API 模式…")

    if resp and resp.ok:
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article.Box-row")
        if articles:
            now = datetime.now().isoformat(timespec="seconds")
            repos: list[TrendingRepo] = []

            for rank, article in enumerate(articles, start=1):
                h2 = article.select_one("h2 a")
                if not h2:
                    continue
                repo_path = h2.get("href", "").strip("/")
                full_url = f"https://github.com/{repo_path}"

                desc_el = article.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                lang_el = article.select_one('[itemprop="programmingLanguage"]')
                lang = lang_el.get_text(strip=True) if lang_el else ""

                star_link = article.select_one('a[href$="/stargazers"]')
                stars_total = _parse_number(star_link.get_text()) if star_link else 0

                fork_link = article.select_one('a[href$="/forks"]')
                forks = _parse_number(fork_link.get_text()) if fork_link else 0

                today_el = article.select_one("span.d-inline-block.float-sm-right")
                stars_today_text = today_el.get_text(strip=True) if today_el else "0"
                stars_today = _parse_number(re.sub(r"[^0-9kK.,]", "", stars_today_text))

                repos.append(
                    TrendingRepo(
                        rank=rank,
                        name=repo_path,
                        description=description,
                        language=lang,
                        stars_total=stars_total,
                        stars_today=stars_today,
                        forks=forks,
                        url=full_url,
                        fetched_at=now,
                    )
                )
            return repos

    # ── 方式 2：第三方 API ────────────────────────────
    try:
        return fetch_trending_api(language=language, since=since, session=session)
    except Exception as exc:
        print(f"[tracker] API 模式也失败了：{exc}")
        raise RuntimeError("无法获取 GitHub Trending 数据，请检查网络连接或配置代理（HTTPS_PROXY 环境变量）")


def save_json(repos: list[TrendingRepo], output_dir: str = "data", tag: str = "") -> Path:
    """将结果序列化为 JSON，文件名含时间戳。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trending_{tag}_{ts}.json" if tag else f"trending_{ts}.json"
    path = out / filename
    data = [asdict(r) for r in repos]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[tracker] 已保存 {len(repos)} 条记录 → {path}")
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="抓取 GitHub Trending")
    parser.add_argument("--lang", default="", help="语言过滤，如 python / go")
    parser.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--output", default="data", help="输出目录")
    args = parser.parse_args()

    repos = fetch_trending(language=args.lang, since=args.since)
    tag = args.lang or "all"
    save_json(repos, output_dir=args.output, tag=f"{tag}_{args.since}")

    print(f"\n今日 Top 5（{args.since}）：")
    for r in repos[:5]:
        print(f"  #{r.rank} {r.name}  ★{r.stars_total}  +{r.stars_today} today  [{r.language}]")
