---
name: context-compressor
description: >
  This skill teaches CodeBuddy to intelligently compress long tool outputs
  and conversation context to reduce token costs. Inspired by Headroom's
  content-aware compression techniques, it should be used when the conversation
  context grows large (>10 messages) or when tool outputs contain large data
  (JSON arrays, lint results, search results, code files, logs, diffs).
triggers:
  - 压缩上下文
  - compress context
  - token optimization
  - large tool outputs
---

# Context Compressor — 上下文压缩技能

## 目的

本技能教导 CodeBuddy 如何智能压缩工具输出和对话上下文，以降低 token 消耗。
核心思想来自 Headroom 项目：**不搞一刀切，根据内容类型选择最优压缩策略**。

### 核心能力

| 能力 | 说明 |
|------|------|
| **7 种内容类型检测** | JSON/代码/lint/日志/搜索/diff/文本，自动识别 |
| **智能路由压缩** | 每种类型专用压缩器，保留关键信息 |
| **三级存储 (CCR)** | L1 热存储(memory 15min) → L2 冷存储(SQLite 2h) → L3 移除 |
| **会话统计** | 累计 token 节省、按类型统计、热/冷存储状态、费用预估 |
| **缓存管理** | 热/冷两级缓存 + 手动清除 + 按类型查询 |

## 何时使用

当出现以下任一情况时，应主动应用压缩：

1. 对话历史超过 10 条消息
2. 单个工具输出超过 500 tokens
3. `read_file` 返回超过 200 行的代码文件
4. `search_content` 或 `search_file` 返回超过 20 条结果
5. `read_lints` 返回超过 10 条诊断信息
6. 用户明确要求压缩或优化 token

## 核心压缩原则

### 原则 1：保护最近对话

永远不压缩最近 3 轮对话（6 条消息），它们包含最重要的上下文。

### 原则 2：按内容类型路由

根据工具输出的内容类型，采用不同的压缩策略：

| 内容类型 | 检测方式 | 压缩策略 | 目标压缩率 |
|----------|---------|---------|-----------|
| JSON 数组 | 以 `[` 开头且可 JSON 解析 | 统计摘要 + 异常保留 + 首尾边界 | 70-90% |
| 代码文件 | read_file 输出 | 保留函数签名 + 折叠函数体 | 取决于代码 |
| lint/诊断 | read_lints 输出 | 按严重级别分组，每种最多 5 条 | 60-80% |
| 搜索结果 | search 类工具 | 按文件分组，每文件最多 5 条匹配 | 50-70% |
| 日志/终端 | 含时间戳/ERROR 模式 | 保留 ERROR/WARN，折叠 INFO | 80-95% |
| diff 输出 | `diff --git` 标记 | 保留代码 diff，丢弃 lockfile | 50-80% |
| 自由文本 | 其他 | 保留首 25% + 尾 15% | 30-50% |

### 原则 3：阈值保护

- 小于 250 tokens 的内容不压缩
- 小于 5 项的 JSON 数组不压缩
- 小于 100 行的文件不折叠函数体
- 小于 50 行的 diff 不做 lockfile 过滤

### 原则 4：三级存储 (CCR 可逆压缩)

```
新数据 ──→ [L1 热存储 Memory] ──溢出──→ [L2 冷存储 SQLite] ──过期──→ [L3 移除]
              │  150条/30MB              │  200MB/SQLite        │
              │  TTL: 15min              │  TTL: 2h             │
              │  └── 检索命中 ──→ 正常返回  │  └── 检索命中 ──→ 提升到热存储
              │  └── 过期 ──→ 溢出到冷存储  │  └── 过期 ──→ 永久移除
```

**存储策略详解：**

| 层级 | 介质 | 上限 | TTL | 适用场景 |
|------|------|------|-----|---------|
| **L1 热存储** | Memory (OrderedDict) | 150 条 / 30MB | 15 分钟 | 最近、最频繁访问的数据 |
| **L2 冷存储** | SQLite Disk | 200MB 上限/按频率淘汰 | 2 小时 | 溢出的大数据、不常访问的历史 |
| **L3 已移除** | — | — | — | 过期或手动清除，不可恢复 |

**数据流向：**
1. 新数据总是先进入 L1 热存储
2. 当热存储满（>150 条 或 >30MB）时，LRU 条目溢出到 L2 冷存储
3. 超过 300KB 的大条目直接存入 L2 冷存储
4. 从冷存储检索时，数据自动提升回 L1 热存储
5. L1 热存储过期（15min）→ 溢出到 L2 冷存储
6. L2 冷存储过期（2h）→ 永久移除
7. 超过 2MB 的单条数据被直接拒绝

**为什么需要冷存储？**
- 大型项目可能有数百个文件，一次性分析会产生大量缓存条目
- 纯内存缓存（30MB）容易被大项目击穿
- SQLite 冷存储可以容纳更多条目，且支持按类型索引查询
- 冷存储有更长的 TTL（2小时），适合长时间开发会话

### 原则 5：统计可观测

每次压缩后更新会话统计，可随时查看：
- 累计压缩次数和 token 节省总量
- 按内容类型的详细统计
- 热/冷两级存储状态（条目数、内存、溢出/提升/命中次数）
- 预估节省费用

## 操作流程

### Step 1: 评估是否需要压缩

在处理工具输出时，检查内容大小。如果超过阈值，触发压缩。

### Step 2: 检测内容类型

对内容进行快速分析，确定属于哪种类型。

### Step 3: 应用对应压缩器

调用 `compress_content` 工具执行压缩。根据类型自动选择最优策略。

### Step 4: 报告压缩效果

在压缩输出末尾自动附加统计信息：
```
[Compressed: 3500 -> 800 tokens (77% saved) | key: a1b2c3d4e5f6]
```

### Step 5: 定期查看统计

当用户询问压缩效果时，调用 `get_compression_stats` 展示统计报告。

## MCP 工具参考

### `compress_content` — 压缩内容

```json
{
  "content": "...大量内容...",
  "content_type": "json"  // 可选：json/code/lint/log/search/diff/text
}
```

### `retrieve_full_content` — 检索原始内容（三级查找）

```json
{
  "cache_key": "a1b2c3d4e5f6"
}
```

> 检索流程：L1 热存储 → L2 冷存储 → None。命中冷存储时自动提升到热存储。

### `detect_type` — 检测内容类型

```json
{
  "content": "...要检测的内容..."
}
```

### `get_compression_stats` — 查看统计报告

```json
{
  "format": "text"  // "text" 或 "json"
}
```

返回示例（text 格式）：

```
+----------------------------------------------------------+
| [*] Context Compression Statistics                     |
+----------------------------------------------------------+
| Session: 0min  |  Compressions: 1                      |
| Tokens:    5,191  ->       315                         |
| SAVED:    4,876 tokens  (94%)                          |
| Est. cost saved: ~$0.015                               |
+----------------------------------------------------------+
| By Content Type:                                       |
|  JSON       1x   4,876t saved (94%)                    |
+----------------------------------------------------------+
| Cache (Tiered Storage):                                |
|  [Hot]  150/150 entries      ~569KB / 29296KB          |
|  Hits: 4  Hot: 4  Miss: 2                             |
|  Get avg: 150μs  Put avg: 85μs                         |
|  [Cold] 103 entries          ~570KB (0%) TTL:7200s     |
|  Spill: 103 Promote: 1       Hit: 1 Evict: 0           |
|  Cold get: 2 Exp: 0 Rej: 0                             |
+----------------------------------------------------------+
| Recent (last 5):                                       |
|  11:41:40  json     5191->315 t (-94%)                 |
+----------------------------------------------------------+
```

### `get_tier_summary` — 查看三级存储状态

```json
{}
```

返回热存储和冷存储的详细状态。

### `cold_query` — 查询冷存储

```json
{
  "content_type": "code",
  "limit": 100  // 可选，默认 100
}
```

按内容类型精确查询冷存储条目。

### `clear_cache` — 清除缓存

```json
{
  "cache_key": "a1b2c3d4e5f6"   // 可选：清除特定条目
}
// 不提供 cache_key 则清除全部缓存（热+冷）
```

### `list_cached` — 列出缓存

```json
{
  "max_entries": 20   // 可选，默认 50
}
```

每个条目包含 `tier` 字段标识存储层级（hot/cold）。

## 使用示例

### 示例 1: 压缩大代码文件

```
原始: read_file 返回 500 行 Python 代码，约 3500 tokens

压缩后:
## query_service.py (500行 → 保留函数签名的概览)

### 函数定义:
- execute_query(sql, params) → QueryResult (第 15-42 行)
  ... 3 lines of body ...
  // ... 22 lines folded
}
- validate_sql(sql) → bool (第 45-68 行)
  ... 3 lines of body ...
  // ... 18 lines folded
}
... 共 25 个函数

// [23 function bodies folded — original 500 lines]
[Compressed: 3500 -> 800 tokens (77% saved) | key: a1b2c3d4e5f6]
```

### 示例 2: 压缩 lint 输出

```
原始: 47 条 lint 诊断信息，约 2000 tokens

压缩后:
## Lint 诊断摘要 (47 → 23 条展示)

### ERROR (3 条):
  - src/service.go:45 - undefined: context.WithTimeout
  - src/handler.go:120 - cannot use err (type error) as string
  - src/db.go:89 - sql.DB.Close() 返回值未检查

### WARNING (8 条，展示前 5):
  - src/utils.go:23 - unused parameter 'ctx'
  - src/config.go:67 - redundant type declaration
  ... 还有 3 条 warning

### INFO/HINT (36 条，已折叠):
  36 条提示信息已折叠

[Compressed: 2000 -> 350 tokens (82% saved) | key: b2c3d4e5f6a7]
```

### 示例 3: 查看压缩统计

用户问："压缩了多少了？"→ 调用 `get_compression_stats`

输出为表格形式的统计报告，展示累计节省、按类型统计、三级存储状态、最近记录。

## 文件结构

```
.codebuddy/skills/context-compressor/
├── SKILL.md                         # 本文件 — 技能定义
└── scripts/
    ├── compress.py                  # 核心压缩引擎 + 三级存储 + 统计
    └── mcp_compress_server.py       # MCP Server (8 个工具)
```

## 注意事项

1. **安全优先**：压缩不得改变代码语义或删除错误信息
2. **保留异常**：ERROR、WARN、异常值必须保留，这些是调试关键
3. **JSON 保底**：JSON 数组中保留前 3 + 后 2 项，以便理解数据范围
4. **代码命名**：保留所有导出的函数/类型/接口名称
5. **不要过度压缩**：当用户明确要求完整内容时，不要压缩
6. **热存储有时效**：15 分钟后溢出到冷存储，2 小时后完全移除
7. **大内容走冷存储**：超过 300KB 自动进冷存储，超过 2MB 被拒绝
8. **冷存储有索引**：可按内容类型查询 SQLite 冷存储中的条目
9. **统计不持久化**：MCP Server 重启后统计归零，但冷存储的 SQLite 文件保留
