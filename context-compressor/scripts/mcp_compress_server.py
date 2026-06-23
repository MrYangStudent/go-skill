"""
MCP Server for context compression — provides compress/retrieve/stats/tier tools to CodeBuddy.

This implements the CCR (Compress-Cache-Retrieve) pattern from Headroom as an MCP server,
with three-tier storage: Hot (memory) → Cold (SQLite) → Evicted (gone).

Features:
  - compress_content: Compress content with auto-type detection
  - retrieve_full_content: Retrieve original content by cache key (hot + cold lookup)
  - detect_type: Detect content type without compressing
  - get_compression_stats: View session compression statistics (with tier breakdown)
  - get_tier_summary: View hot/cold storage breakdown
  - cold_query: Query cold storage by content type
  - clear_cache: Manually clear cached entries (both tiers)
  - list_cached: Inspect cache contents (both tiers with tier labels)

Usage:
    python mcp_compress_server.py

Configure in CodeBuddy's .mcp.json:
    {
      "mcpServers": {
        "context-compressor": {
          "command": "python3",
          "args": ["path/to/mcp_compress_server.py"]
        }
      }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any

# Force UTF-8 on stdout so Chinese tool descriptions render correctly
# even when the default console code page is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Import the compress module from the same skill
from compress import (  # type: ignore[import-untyped]
    compress,
    retrieve_original,
    store_original,
    clear_cache,
    list_cached_entries,
    get_stats_json,
    get_stats_summary,
    detect_content_type,
    get_tier_summary,
    cold_query_by_type,
    ContentType,
    CompressResult,
    HOT_TTL_SECONDS,
    COLD_TTL_SECONDS,
    HOT_MAX_ENTRIES,
    HOT_MAX_BYTES,
    HOT_MAX_ENTRY_BYTES,
    HOT_SPILL_BATCH,
    COLD_MAX_ENTRY_BYTES,
    COLD_MAX_TOTAL_BYTES,
    COLD_EVICT_BATCH,
)


def _compress_result_to_dict(result: CompressResult) -> dict[str, Any]:
    """Convert CompressResult to a JSON-safe dictionary."""
    return {
        "compressed_content": result.content,
        "original_tokens": result.original_tokens,
        "compressed_tokens": result.compressed_tokens,
        "tokens_saved": result.tokens_saved,
        "saved_pct": round(result.saved_pct, 1),
        "cache_key": result.cache_key,
        "content_type": result.content_type.value,
        "truncated_items": result.truncated_items,
        "note": (
            "Original cached for CCR retrieval | "
            f"Cache key: {result.cache_key}"
        ),
    }


def _make_text_result(data: Any) -> dict[str, Any]:
    """Wrap a result as JSON text content for MCP response."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(data, ensure_ascii=False, indent=2),
            }
        ]
    }


def _make_error(message: str) -> dict[str, Any]:
    """Create an error response."""
    return {
        "content": [
            {"type": "text", "text": f"[ERROR] {message}"}
        ]
    }


def _handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "context-compressor",
                    "version": "3.0.0",
                },
                "capabilities": {
                    "tools": {},
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "compress_content",
                        "description": (
                            "压缩工具输出或文本内容，降低 token 消耗。\n"
                            "支持 7 种内容类型：JSON 数组、代码文件、lint 诊断、"
                            "日志、搜索结果、diff 输出、自由文本。\n"
                            "根据内容类型自动选择最优压缩策略。\n"
                            "返回压缩后的内容、token 节省数据、缓存 key。\n"
                            "三级存储：数据存于热存储(memory, 15min TTL)，"
                            "溢出到冷存储(SQLite disk, 2h TTL, 200MB 上限)。\n"
                            f"批量溢出：每次 {HOT_SPILL_BATCH} 条，冷存储超限按访问频率淘汰。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "要压缩的原始内容",
                                },
                                "content_type": {
                                    "type": "string",
                                    "enum": [t.value for t in ContentType],
                                    "description": "内容类型提示，省略则自动检测",
                                },
                            },
                            "required": ["content"],
                        },
                    },
                    {
                        "name": "retrieve_full_content",
                        "description": (
                            f"通过 cache_key 检索之前压缩的完整原始内容。\n"
                            f"三级存储检索流程：\n"
                            f"  1) 优先查热存储(memory, TTL={HOT_TTL_SECONDS}s)\n"
                            f"  2) 热存储未命中则查冷存储(SQLite disk, TTL={COLD_TTL_SECONDS}s)\n"
                            f"  3) 冷存储命中后自动提升到热存储\n"
                            f"热存储上限 {HOT_MAX_ENTRIES} 条/{HOT_MAX_BYTES//1048576}MB，批量溢出 {HOT_SPILL_BATCH} 条/次。\n"
                            f"单条目 >{HOT_MAX_ENTRY_BYTES//1024}KB 直接进冷存储。\n"
                            f"冷存储单条目上限 {COLD_MAX_ENTRY_BYTES//1048576}MB，总上限 {COLD_MAX_TOTAL_BYTES//1048576}MB，\n"
                            f"超限时按访问频率淘汰（每批 {COLD_EVICT_BATCH} 条）。\n"
                            f"如未找到则返回错误信息。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "cache_key": {
                                    "type": "string",
                                    "description": "压缩时返回的 cache_key（12 位 hex）",
                                },
                            },
                            "required": ["cache_key"],
                        },
                    },
                    {
                        "name": "detect_type",
                        "description": (
                            "检测给定内容的类型，返回检测结果。"
                            "无需压缩即可了解内容类型，供决策使用。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "要检测的内容",
                                },
                            },
                            "required": ["content"],
                        },
                    },
                    {
                        "name": "get_compression_stats",
                        "description": (
                            "获取当前会话的压缩统计报告。包括：\n"
                            "- 累计压缩次数和 token 节省总量\n"
                            "- 按内容类型的详细统计\n"
                            "- 预估节省费用\n"
                            "- 热存储状态（条目数、内存占用、命中率、延迟）\n"
                            "- 冷存储状态（条目数、磁盘占用、溢出/提升/检索、大小淘汰）\n"
                            "- 分 tier 命中率（hot/cold hits）\n"
                            "- 操作延迟（get/put avg μs）\n"
                            "- 最近压缩记录时间线\n"
                            "支持 text 和 json 两种格式输出。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "format": {
                                    "type": "string",
                                    "enum": ["text", "json"],
                                    "description": "输出格式：text（可读报告）或 json（结构化数据）",
                                },
                            },
                        },
                    },
                    {
                        "name": "get_tier_summary",
                        "description": (
                            "获取三级存储的详细状态。返回：\n"
                            "- 热存储：条目数、内存占用、上限、TTL\n"
                            "- 冷存储：条目数、磁盘占用、溢出次数、提升次数、" 
                            "检索命中次数、拒绝次数\n"
                            "- 总览：总条目数和总占用\n"
                            "用于监控存储健康状态和排查性能问题。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                    {
                        "name": "cold_query",
                        "description": (
                            "按内容类型查询冷存储中的条目。" 
                            "返回 key、大小、存储时间等元数据。" 
                            "用于分析冷存储中的数据类型分布。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content_type": {
                                    "type": "string",
                                    "enum": [t.value for t in ContentType],
                                    "description": "要查询的内容类型",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "最多返回条目数（默认 100）",
                                },
                            },
                            "required": ["content_type"],
                        },
                    },
                    {
                        "name": "clear_cache",
                        "description": (
                            "清除指定或全部缓存条目（同时清除热存储和冷存储）。" 
                            "可选参数 cache_key 清除特定条目，"
                            "不提供则清除全部缓存并释放内存和磁盘空间。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "cache_key": {
                                    "type": "string",
                                    "description": "要清除的特定缓存 key，不提供则清除全部",
                                },
                            },
                        },
                    },
                    {
                        "name": "list_cached",
                        "description": (
                            "列出当前缓存中的条目信息（热存储+冷存储）。" 
                            "每个条目包含：key、大小、存储时长、过期倒计时、"
                            "内容类型、存储层级(hot/cold)。"
                            "用于检查缓存状态和排查问题。"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "max_entries": {
                                    "type": "integer",
                                    "description": "最多返回的条目数（默认 50）",
                                },
                            },
                        },
                    },
                ],
            },
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # ── compress_content ─────────────────────────────────────────
        if tool_name == "compress_content":
            content = arguments.get("content", "")
            ctype_str = arguments.get("content_type")
            ctype = ContentType(ctype_str) if ctype_str else None
            result = compress(content, ctype)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _make_text_result(_compress_result_to_dict(result)),
            }

        # ── retrieve_full_content ────────────────────────────────────
        if tool_name == "retrieve_full_content":
            cache_key = arguments.get("cache_key", "")
            original = retrieve_original(cache_key)
            if original is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": _make_error(
                        f"未找到缓存 key '{cache_key}'。可能原因：\n"
                        f"  1) 热存储已过期（TTL={HOT_TTL_SECONDS}s）且未存入冷存储\n"
                        f"  2) 冷存储已过期（TTL={COLD_TTL_SECONDS}s）\n"
                        f"  3) 溢出时磁盘空间不足，条目永久丢失\n"
                        f"  4) 从未以此 key 存储过数据"
                    ),
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "cache_key": cache_key,
                                    "original_content": original,
                                    "size_chars": len(original),
                                    "note": "此为原始完整内容，未压缩",
                                },
                                ensure_ascii=False,
                                indent=2,
                            ),
                        }
                    ]
                },
            }

        # ── detect_type ──────────────────────────────────────────────
        if tool_name == "detect_type":
            content = arguments.get("content", "")
            ctype = detect_content_type(content)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _make_text_result({
                    "content_type": ctype.value,
                    "sample_preview": content[:200],
                    "total_length": len(content),
                }),
            }

        # ── get_compression_stats ────────────────────────────────────
        if tool_name == "get_compression_stats":
            fmt = arguments.get("format", "text")
            if fmt == "json":
                data = get_stats_json()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": _make_text_result(data),
                }
            else:
                summary = get_stats_summary()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": summary}]
                    },
                }

        # ── get_tier_summary ─────────────────────────────────────────
        if tool_name == "get_tier_summary":
            data = get_tier_summary()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _make_text_result(data),
            }

        # ── cold_query ───────────────────────────────────────────────
        if tool_name == "cold_query":
            ctype = arguments.get("content_type", "")
            limit = arguments.get("limit", 100)
            results = cold_query_by_type(ctype, limit)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _make_text_result({
                    "content_type": ctype,
                    "count": len(results),
                    "entries": results,
                }),
            }

        # ── clear_cache ──────────────────────────────────────────────
        if tool_name == "clear_cache":
            cache_key = arguments.get("cache_key")
            if cache_key:
                # Remove specific entry (both tiers)
                from compress import _cache  # type: ignore[import-untyped]
                removed = _cache.remove(cache_key)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": _make_text_result({
                        "action": "remove_single",
                        "cache_key": cache_key,
                        "removed": removed,
                        "message": (
                            f"Removed entry {cache_key} from all tiers"
                            if removed
                            else f"Entry {cache_key} not found in any tier"
                        ),
                    }),
                }
            else:
                result = clear_cache()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": _make_text_result({
                        "action": "clear_all",
                        **result,
                        "message": f"Cleared all {result['removed_entries']} entries from hot + cold tiers",
                    }),
                }

        # ── list_cached ──────────────────────────────────────────────
        if tool_name == "list_cached":
            max_entries = arguments.get("max_entries", 50)
            entries = list_cached_entries(max_entries)
            from compress import _cache, get_tier_summary  # type: ignore[import-untyped]
            tier = get_tier_summary()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _make_text_result({
                    "total_cached": _cache.entry_count,
                    "total_bytes": _cache.total_bytes,
                    "hot_count": _cache.hot_count,
                    "cold_count": _cache.cold_count,
                    "entries": entries,
                }),
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    """Run the MCP server over stdio (JSON-RPC)."""
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = _handle_request(request)
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception:
            # Try to recover with an error response
            req_id = None
            try:
                req_id = json.loads(line.strip()).get("id")
            except Exception:
                pass
            error_response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": "Internal server error processing request",
                },
            }
            sys.stdout.write(json.dumps(error_response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
