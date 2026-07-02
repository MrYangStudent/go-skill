---
name: github-trend-monitor
description: GitHub Trending 趋势监控技能，自动抓取趋势项目、AI 生成简报、邮件推送日报、星标激增检测和可视化仪表盘。当用户要求监控 GitHub 趋势、生成趋势日报、分析技术趋势或配置趋势告警时触发。
triggers:
  - GitHub Trending
  - 趋势监控
  - 趋势日报
  - 趋势简报
  - github trend
  - 趋势分析
  - 星标激增
  - GitHub 趋势
---

# GitHub Trending 趋势监控技能

> 自动抓取 GitHub Trending → AI 分析生成简报 → 邮件推送日报 → 可视化仪表盘

## 功能概述

本技能提供完整的 GitHub Trending 趋势监控能力：

| 模块 | 功能 |
|------|------|
| **Tracker** | 爬取 GitHub Trending（支持日/周/月榜、语言过滤） |
| **Summarizer** | AI 生成趋势简报（支持 OpenAI 及兼容 API） |
| **Sender** | SMTP 邮件发送（HTML 格式、图表嵌入） |
| **Alert** | 星标激增检测（对比历史、发现异常增长） |
| **Analyzer** | 技术栈趋势分析（语言分布、领域聚类、跨期对比） |
| **Chart** | 生成图表 PNG（语言分布、领域分布、Top 项目） |
| **Dashboard** | 交互式 HTML 仪表盘（多图表、时间线趋势） |

## 使用场景

### 场景 1：快速生成趋势日报

**需求**：抓取今日 GitHub Trending，生成 AI 简报并发送邮件

```bash
python main.py pipeline
```

**参数**：
- `--lang` - 语言过滤，如 `python`、`go`、`typescript`
- `--since` - 榜单时间：`daily`（默认）/ `weekly` / `monthly`
- `--top` - AI 分析前 N 条（默认 25）
- `--no-send` - 只生成简报，不发送邮件
- `--to` - 指定收件人（逗号分隔）

**示例**：
```bash
# 只抓 Go 项目，生成简报不发邮件
python main.py pipeline --lang go --no-send

# 周榜，分析前 30 条
python main.py pipeline --since weekly --top 30

# 指定收件人
python main.py pipeline --to user1@example.com,user2@example.com
```

### 场景 2：星标激增告警

**需求**：检测今日相比昨日星标增速异常的项目

```bash
python main.py alert
```

**参数**：
- `--threshold` - 增速倍数阈值（默认 2.0，即 2 倍）
- `--top` - 最多 N 条告警（默认 10）
- `--no-send` - 只输出不发送邮件

**示例**：
```bash
# 增速 ≥ 3 倍才告警
python main.py alert --threshold 3.0

# 只看 Top 5 告警
python main.py alert --top 5
```

### 场景 3：技术栈趋势分析

**需求**：分析 Trending 项目的语言、领域分布，识别技术趋势

```bash
python main.py analyze
```

**参数**：
- `--compare` - 对比上期数据
- `--ai` - AI 增强分析（调用 LLM 生成趋势解读）
- `--lang` - 语言过滤
- `--no-send` - 不发送邮件

**示例**：
```bash
# 对比 + AI 增强分析
python main.py analyze --compare --ai

# 只分析 Python 项目
python main.py analyze --lang python
```

### 场景 4：可视化仪表盘

**需求**：生成交互式 HTML 仪表盘，查看多维度趋势

```bash
python main.py dashboard
```

**参数**：
- `--output` - 输出文件名（默认 `dashboard.html`）
- `--lang` - 语言过滤

**示例**：
```bash
# 生成仪表盘
python main.py dashboard

# 只看 Python 项目
python main.py dashboard --lang python --output python_dashboard.html
```

### 场景 5：每日汇总（完整流程）

**需求**：一次性执行所有模块，生成完整日报并发送汇总邮件

```bash
python run_daily.py
```

**参数**：
- `--lang` - 语言过滤
- `--since` - 榜单时间
- `--top` - AI 分析前 N 条
- `--alert-threshold` - 激增告警阈值
- `--no-send` - 只生成不发邮件

**执行流程**：
1. Pipeline：抓取 Trending → AI 生成趋势简报
2. Alert：星标激增检测
3. Analyze：技术栈分析（含跨期对比 + AI 解读）
4. Charts：生成图表 PNG
5. Dashboard：生成可视化仪表盘
6. 合并所有报告 + 嵌入图表 → 发送汇总邮件

## 环境配置

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 openai python-dotenv matplotlib
# 可选，Markdown 渲染更好看
pip install markdown
# 可选，安全存储密钥
pip install keyring
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.openai.com/v1  # 或兼容接口
SUMMARIZER_MODEL=gpt-4o-mini

# SMTP 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@example.com
SMTP_PASS=your_smtp_password  # QQ 邮箱用授权码

# 收件人
DIGEST_TO=user1@example.com,user2@example.com
```

### 3. 安全存储密钥（可选）

使用 keyring 安全存储敏感凭据：

```python
from secrets import set_secret, get_secret

# 存储
set_secret("OPENAI_API_KEY", "sk-xxxxx")
set_secret("SMTP_PASS", "your_password")

# 读取
api_key = get_secret("OPENAI_API_KEY")
```

## 输出结构

```
github-trend-monitor/
├── data/           # JSON 原始数据（按时间戳命名）
│   └── trending_all_daily_20260520_133922.json
├── reports/        # Markdown 简报
│   ├── report_daily_20260520_133922.md
│   └── tech_stack_20260520_142125.md
├── alerts/         # 激增告警报告
│   └── alert_20260520_142117.md
├── charts/         # 图表 PNG
│   ├── lang_distribution.png
│   ├── domain_distribution.png
│   └── top_repos.png
├── dashboard.html  # 可视化仪表盘
└── .env            # 环境变量（勿提交）
```

## 核心 API

### Tracker 模块

```python
from tracker import fetch_trending, save_json

# 抓取 Trending
repos = fetch_trending(language="python", since="daily")

# 保存为 JSON
json_path = save_json(repos, output_dir="data", tag="python_daily")
```

### Summarizer 模块

```python
from summarizer import summarize, summarize_from_file

# 直接生成简报
content = summarize(repos, since="daily", top_n=25)

# 从 JSON 文件生成
md_path = summarize_from_file(json_path, since="daily", top_n=25)
```

### Sender 模块

```python
from sender import send_digest, send_from_file

# 发送邮件
send_digest(md_content="# 简报内容", subject="GitHub 趋势日报")

# 从文件发送
send_from_file("reports/report.md", to_addrs=["user@example.com"])
```

### Alert 模块

```python
from alert_on_spike import detect_spikes, run_alert

# 检测激增
report = detect_spikes(data_dir="data", threshold=2.0, top_n=10)

# 执行并发送告警
report = run_alert(data_dir="data", threshold=2.0, no_send=False)
```

### Analyzer 模块

```python
from tech_stack_analyzer import analyze_snapshot, run_analysis

# 分析快照
report = analyze_snapshot(repos, lang_filter="python")

# 执行分析
report = run_analysis(data_dir="data", compare=True, ai_enhanced=True)
```

### Chart 模块

```python
from chart_generator import generate_charts

# 生成图表
chart_paths = generate_charts(data_dir="data", output_dir="charts")
# 返回: {"lang": "charts/lang_distribution.png", ...}
```

### Dashboard 模块

```python
from trend_dashboard_builder import build_dashboard

# 生成仪表盘
dash_path = build_dashboard(data_dir="data", output="dashboard.html")
```

## 定时任务

### Linux/macOS（Cron）

```bash
# 每天早上 8:00 自动运行
crontab -e
# 添加：
0 8 * * * cd /path/to/github-trend-monitor && python main.py pipeline >> logs/cron.log 2>&1
```

### Windows（任务计划程序）

```powershell
# 创建每日 8:00 任务
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
$action = New-ScheduledTaskAction -Execute "python" -Argument "D:\path\to\main.py pipeline"
Register-ScheduledTask -TaskName "GitHubTrend" -Trigger $trigger -Action $action
```

## 技术细节

### 数据抓取策略

1. **优先直连**：尝试爬取 GitHub 页面（需网络通畅）
2. **代理支持**：自动读取 `HTTPS_PROXY` / `HTTP_PROXY` 环境变量

### AI 简报生成

- **模型**：默认 `gpt-4o-mini`，可通过 `SUMMARIZER_MODEL` 或 `--model` 参数指定
- **兼容接口**：支持 OpenAI 及任意兼容 OpenAI 协议的接口（如 Azure、VLLM 等）
- **Prompt 策略**：结构化输出，包含整体概述、重点项目、技术趋势三部分

### 邮件发送

- **SMTP 支持**：QQ 邮箱 / 163 / Gmail / 企业邮箱
- **HTML 格式**：暗色主题，内联样式，兼容主流邮件客户端
- **图表嵌入**：PNG 图片通过 CID 方式嵌入邮件

## 参考代码

参考代码位于 `reference/` 目录：

| 文件 | 说明 |
|------|------|
| `reference/tracker.py` | 爬虫核心实现 |
| `reference/summarizer.py` | AI 简报生成 |
| `reference/sender.py` | 邮件发送 |
| `reference/alert_on_spike.py` | 激增检测 |
| `reference/tech_stack_analyzer.py` | 技术栈分析 |
| `reference/chart_generator.py` | 图表生成 |
| `reference/trend_dashboard_builder.py` | 仪表盘构建 |
| `reference/secrets.py` | 密钥管理 |

## 故障排查

### 问题：网络请求失败

```bash
# 设置代理
export HTTPS_PROXY=http://127.0.0.1:7890
python main.py pipeline
```

### 问题：AI 分析失败

1. 检查 `OPENAI_API_KEY` 是否正确
2. 检查网络是否能访问 OpenAI API
3. 查看错误日志，确认是 API 错误还是网络问题

### 问题：邮件发送失败

1. 确认 SMTP 配置正确（HOST、PORT、USER、PASS）
2. QQ 邮箱需使用**授权码**而非登录密码
3. 检查是否被邮箱服务商拦截

### 问题：图表中文显示方块

确保系统安装了中文字体：
- Windows：微软雅黑 (`C:/Windows/Fonts/msyh.ttc`)
- Linux：安装 `fonts-wqy-microhei` 或 `fonts-wqy-zenhei`
