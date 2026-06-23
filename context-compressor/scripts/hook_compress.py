"""
Hook adapter for context-compressor — multi-platform Hooks integration.

Supports CodeBuddy, Claude Code, and OpenAI Codex through a unified stdin-JSON
protocol.  All three platforms share the same event names, input format, and
``additionalContext`` injection mechanism (with minor output-format differences).

Platform support:
  - CodeBuddy   → ``~/.codebuddy/settings.json``  (install: ``--codebuddy``)
  - Claude Code → ``~/.claude/settings.json``      (install: ``--claude``)
  - OpenAI Codex→ ``~/.codex/hooks.json``          (install: ``--codex``)

Protocol:
  - Receives JSON via stdin (Hook event data).
  - Outputs JSON via stdout (Hook response with ``additionalContext`` at
    top-level for CodeBuddy, and ``hookSpecificOutput`` nested for Claude
    Code / Codex).

Usage:
    # Configured via install.py or manually in settings.json / hooks.json.
    # The IDE/CLI calls this script automatically on Hook events.

    python install.py            # auto-detect and install
    python install.py --claude   # Claude Code only
    python install.py --codex    # Codex only

Events handled:
  - PreToolUse    →  lightweight pass-through (cache warming is deferred to MCP).
  - PostToolUse   →  detects large tool output, rule-compresses it, persists the
                      original to cold store, and injects the compressed content
                      into additionalContext for immediate LLM reasoning.
  - PreCompact    →  notifies agent that cached data is available.
  - Stop          →  materialises today's cold_entries into daily_stats (SQLite),
                      and produces a session-end summary with token savings.
  - SessionStart  →  queries daily_stats for yesterday's / today's data so the
                      agent has context about compression history.
"""

from __future__ import annotations

import json
import os
import sys

# ── Make compress module importable from the same directory ──────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from compress import (  # noqa: E402
    ContentType,
    _resolve_workspace,
    compress,
    estimate_tokens,
    persist_to_cold,
)

from daily_report import (  # noqa: E402
    get_yesterday_stats_summary,
    persist_daily_stats,
)

# ── Diagnostic logging (development only) ─────────────────────────────────────


def _diag_log(msg: str) -> None:
    """Write a timestamped diagnostic message to hook_diag.log.

    Purely for debugging whether CodeBuddy actually invokes the hook script.
    Remove or disable for production.

    File size is capped at ~500 KB: when exceeded, the oldest lines are
    trimmed to keep the log from growing unboundedly.
    """
    try:
        from datetime import datetime as _dt
        import os as _os

        _MAX_BYTES = 500_000       # 500 KB
        _KEEP_LINES = 200          # keep most recent ~200 lines after trim

        diag_path = _os.path.normpath(_os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)),
            "..", "cache", "hook_diag.log",
        ))

        # Ensure the cache directory exists.
        _os.makedirs(_os.path.dirname(diag_path), exist_ok=True)

        # Trim if oversized before appending.
        if _os.path.exists(diag_path) and _os.path.getsize(diag_path) > _MAX_BYTES:
            with open(diag_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(diag_path, "w", encoding="utf-8") as f:
                f.writelines(lines[-_KEEP_LINES:])

        with open(diag_path, "a", encoding="utf-8") as f:
            f.write(f"{_dt.now().isoformat()} | {msg}\n")
    except Exception:
        pass


def _wrap_output(hook_event_name: str, result: dict) -> dict:
    """Add ``hookSpecificOutput`` for Claude Code / Codex cross-compatibility.

    CodeBuddy reads ``additionalContext`` from the top level of the JSON output.
    Claude Code and Codex read it from ``hookSpecificOutput.additionalContext``.
    This wrapper ensures both formats are present so the same hook script works
    on all three platforms without modification.

    If the result already has a ``hookSpecificOutput`` key, return as-is.
    """
    if "hookSpecificOutput" in result or "additionalContext" not in result:
        return result

    result["hookSpecificOutput"] = {
        "hookEventName": hook_event_name,
        "additionalContext": result["additionalContext"],
    }
    return result


# ── Configuration ───────────────────────────────────────────────────────────

# Minimum tokens before auto-caching (same as compress module threshold).
COMPRESS_THRESHOLD = 250  # tokens

# Tool name → ContentType mapping for accurate type tagging in cache.
# Maps CodeBuddy tool names (both canonical and IDE-specific aliases)
# to the content-type string used in the CCR cold-store index.
TOOL_TYPE_MAP: dict[str, str] = {
    "read_file": "code",
    "read_lints": "lint",
    "search_content": "search",
    "search_file": "search",
    "execute_command": "log",
    "grep": "search",
    "Read": "code",           # IDE-specific tool aliases
    "Glob": "search",
    "Grep": "search",
    "Bash": "log",
}

# ── String content-type → ContentType enum mapping ────────────────────────────
# The TOOL_TYPE_MAP above uses string values; compress() expects the enum.

_STR_TO_CONTENT_TYPE: dict[str, ContentType] = {
    "code": ContentType.CODE,
    "lint": ContentType.LINT,
    "search": ContentType.SEARCH,
    "log": ContentType.LOG,
    "diff": ContentType.DIFF,
    "text": ContentType.TEXT,
    "json": ContentType.JSON_ARRAY,
    "unknown": ContentType.UNKNOWN,
}


# ── Lenient JSON parsing for malformed large tool_output ──────────────────────


def _parse_event_lenient(raw: str) -> dict:
    """Parse event JSON with fallback for large tool_output with unescaped chars.

    When ``tool_output`` contains unescaped double-quotes or backslashes (common
    with markdown/doc files), ``json.loads`` fails.  This function extracts the
    essential fields from the raw text so the hook can still process the event.
    """
    import re as _re

    event: dict[str, object] = {}

    # Extract simple string fields.
    for field in ("hook_event_name", "tool_name", "session_id"):
        m = _re.search(rf'"{field}"\s*:\s*"([^"]*)"', raw)
        if m:
            event[field] = m.group(1)

    # CodeBuddy uses "tool_output" for read_file and "tool_response" for Bash.
    for out_field in ("tool_output", "tool_response"):
        m = _re.search(rf'"{out_field}"\s*:\s*"', raw)
        if not m:
            continue
        start = m.end()
        # Walk backward from end-of-JSON to find the last field boundary
        # before the closing brace.  The pattern is: ...","next_key":"...", ...}
        # Find the last "} in the raw text and look for ", " patterns before it.
        last = raw.rfind('}')
        if last < start:
            last = len(raw)
        # Scan backward from 'last' for the closing quote of tool_output.
        # The closing quote is followed by "," or "}".  But the content itself
        # may contain ", so we look for the field separator pattern ", "field":"
        # that marks the next JSON key.
        end = last
        known_keys = ["client", "generation_id", "model", "version",
                      "session_id", "transcript_path", "cwd"]
        for nk in known_keys:
            # Pattern: ","key_name":  — this marks the end of the previous value
            pat = f',"{nk}":'
            idx = raw.rfind(pat, start)
            if idx != -1 and idx < end:
                end = idx
        if end > start:
            event["tool_output"] = raw[start:end]
        else:
            event["tool_output"] = raw[start:min(start + 100, last)].rstrip('}"\n\r')
        break  # only process one output field

    # Try to extract tool_input as JSON (for read_file file-path fallback).
    ti = _re.search(r'"tool_input"\s*:\s*(\{[^}]+\})', raw)
    if ti:
        try:
            event["tool_input"] = json.loads(ti.group(1))
        except json.JSONDecodeError:
            pass
    # Also try with nested braces (e.g., {"filePath": "...", "limit": 100}).
    if "tool_input" not in event:
        ti2 = _re.search(r'"tool_input"\s*:\s*(\{.*?\})\s*(?:,|$)', raw)
        if ti2:
            try:
                event["tool_input"] = json.loads(ti2.group(1))
            except json.JSONDecodeError:
                pass

    if not event.get("hook_event_name"):
        event["hook_event_name"] = ""
    if not event.get("tool_name"):
        event["tool_name"] = ""

    return event


# ── Content extraction helpers ───────────────────────────────────────────────


def _extract_content(tool_output: object) -> str | None:
    """Extract human-readable content from a tool_output value.

    Different tools return different structures: bare strings, dicts with
    ``stdout``/``stderr``, objects with ``content`` fields, or arbitrary
    JSON-serialisable types.  This function normalises them to a plain string
    suitable for token counting and caching.

    Returns ``None`` when no meaningful text content can be extracted.
    """
    if tool_output is None:
        return None

    # Bare string — most common for read_file, etc.
    if isinstance(tool_output, str):
        stripped = tool_output.strip()
        return stripped if stripped else None

    # Dict/object with stdout (execute_command, Bash tools).
    if isinstance(tool_output, dict):
        stdout = tool_output.get("stdout")
        if isinstance(stdout, str) and stdout.strip():
            return stdout.strip()
        content = tool_output.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        # Fallback: JSON-serialise and count as text
        try:
            serialised = json.dumps(tool_output, ensure_ascii=False)
            return serialised if len(serialised) > 10 else None
        except (TypeError, ValueError):
            return None

    # List — e.g. search results or lint diagnostics.
    if isinstance(tool_output, list):
        if len(tool_output) == 0:
            return None
        try:
            serialised = json.dumps(tool_output, ensure_ascii=False)
            return serialised
        except (TypeError, ValueError):
            return None

    # Other object — try JSON serialisation.
    try:
        serialised = json.dumps(tool_output, ensure_ascii=False, default=str)
        return serialised if len(serialised) > 10 else None
    except (TypeError, ValueError):
        return None


# ── Event handlers ───────────────────────────────────────────────────────────


def handle_post_tool_use(event: dict) -> dict:
    """Handle PostToolUse: compress large tool outputs and inject into context.

    Strategy:
      1. Extract text content from the tool output.
      2. If it exceeds the token threshold, run rule-based compression
         (no LLM call — 7 heuristic compressors in compress.py).
      3. Persist the ORIGINAL to cold (SQLite) storage for later retrieval.
      4. Inject the COMPRESSED content directly into ``additionalContext``
         so the LLM can reason over it immediately without a follow-up
         MCP retrieval call.  A cache key is still included as fallback.

    The compressed content goes into the conversation context, replacing the
    original (which is too large).  This saves tokens immediately while still
    giving the LLM enough information to work with.
    """
    tool_name = event.get("tool_name", "")
    tool_output = event.get("tool_output") or event.get("tool_response") or {}

    # If tool_output is empty/None and this is a file-read tool, try to
    # re-read the file directly via the path in tool_input.
    if (not tool_output or tool_output == {}) and tool_name.lower() in (
        "read_file", "read", "readfile",
    ):
        tool_input = event.get("tool_input", {})
        file_path = (
            tool_input.get("filePath")
            or tool_input.get("file_path")
            or tool_input.get("path")
        )
        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    tool_output = f.read()
                _diag_log(f"PostToolUse: re-read file {file_path} len={len(str(tool_output))}")
            except Exception as re_ex:
                _diag_log(f"PostToolUse: re-read failed: {re_ex}")

    _diag_log(f"PostToolUse: tool={tool_name} output_type={type(tool_output).__name__} "
              f"len={len(str(tool_output)) if tool_output else 0}")

    content = _extract_content(tool_output)
    if content is None:
        _diag_log("PostToolUse: SKIP — no extractable content")
        return {"continue": True}

    _diag_log(f"PostToolUse: content extracted, len={len(content)}")
    tokens = estimate_tokens(content)
    _diag_log(f"PostToolUse: tokens={tokens} threshold={COMPRESS_THRESHOLD}")
    if tokens < COMPRESS_THRESHOLD:
        _diag_log("PostToolUse: SKIP — below threshold")
        return {"continue": True}

    # Determine content type for proper cache tagging and compression routing.
    content_type_str = TOOL_TYPE_MAP.get(tool_name, "unknown")
    content_type_enum = _STR_TO_CONTENT_TYPE.get(content_type_str, ContentType.UNKNOWN)

    # Step 1: Compress the content (rule-based, no LLM).
    # store=False avoids the in-process hot cache (useless for short-lived hook).
    _diag_log(f"PostToolUse: calling compress(type={content_type_str})")
    cr = compress(content, content_type=content_type_enum, store=False)
    _diag_log(
        f"PostToolUse: compressed {cr.original_tokens}→{cr.compressed_tokens} tokens "
        f"ratio={cr.ratio:.0%} key={cr.cache_key}"
    )

    # Step 2: Persist the ORIGINAL content to cold (SQLite) storage so it
    # survives the hook process and can be retrieved via retrieve_full_content.
    cache_key = persist_to_cold(content, content_type=content_type_str)
    _diag_log(f"PostToolUse: persist_to_cold returned key={cache_key}")

    # Step 3: Inject the COMPRESSED content into the conversation so the LLM
    # can reason over it immediately without a follow-up MCP retrieval call.
    return {
        "continue": True,
        "additionalContext": (
            f"[Hook] {tool_name} 输出已压缩: {cr.original_tokens} → {cr.compressed_tokens} tokens "
            f"(节省 {cr.original_tokens - cr.compressed_tokens}，压缩率 {cr.ratio:.0%})。"
            f"原始数据缓存 key: `{cache_key}`。\n"
            f"---压缩内容---\n"
            f"{cr.content}\n"
            f"---结束---"
        ),
    }


def handle_pre_tool_use(event: dict) -> dict:
    """Handle PreToolUse: optional cache-warming hint.

    Before a tool like read_file or search_content fires, this handler
    does a lightweight check and passes through silently.  Heavy cache
    warming is deferred to the MCP server; the hook only ensures it
    never blocks tool execution.
    """
    return {"continue": True}


def handle_pre_compact(event: dict) -> dict:
    """Handle PreCompact: notify agent about available cached data.

    When CodeBuddy is about to compact the conversation history, the agent
    should be aware that original tool outputs are preserved in the CCR
    tiered cache and can be retrieved on demand.
    """
    return {
        "continue": True,
        "additionalContext": (
            "[PreCompact] Conversation context is being compacted. "
            "Original tool outputs are preserved in the compression cache. "
            "Use `list_cached` to view entries, "
            "`retrieve_full_content` to restore any original, "
            "and `get_compression_stats` for session statistics."
        ),
    }


def _count_today_cold_entries() -> tuple[int, int]:
    """Count cold-store entries stored today and their estimated tokens.

    Returns (count, estimated_tokens) or (0, 0) on any error.
    """
    try:
        import os as _os
        import sqlite3
        import time as _time

        workspace = _resolve_workspace()
        db_path = _os.path.join(
            workspace, ".codebuddy", "skills", "context-compressor",
            "cache", "ccr_shared_cold.db",
        )
        if not _os.path.exists(db_path):
            return 0, 0

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Map monotonic → wall-clock date using boot_epoch trick.
        boot = _time.time() - _time.monotonic()
        today = _time.strftime("%Y-%m-%d", _time.localtime())

        rows = conn.execute(
            "SELECT size_bytes, stored_at FROM cold_entries"
        ).fetchall()
        conn.close()

        count = 0
        tokens = 0
        for r in rows:
            entry_date = _time.strftime(
                "%Y-%m-%d",
                _time.localtime(boot + r["stored_at"]),
            )
            if entry_date == today:
                count += 1
                tokens += max(1, (r["size_bytes"] or 0) // 4)
        return count, tokens
    except Exception:
        return 0, 0


def handle_stop(event: dict) -> dict:
    """Handle Stop: persist stats to daily_stats table + session-end summary.

    On session end, materialise today's cold_entries into the daily_stats
    aggregated table so that query_stats / daily_report have canonical data.
    Then produce a brief summary the next session can pick up.
    """
    # Persist to daily_stats (idempotent — safe to call multiple times).
    ok = persist_daily_stats()
    if not ok:
        return {"continue": True}

    # Read back the stats we just wrote.
    try:
        from datetime import date as _date
        today = _date.today().isoformat()
        results = __import__(
            "daily_report", fromlist=["query_stats"]
        ).query_stats(today, today)
    except Exception:
        results = []

    if not results:
        return {"continue": True}

    total_entries = sum(r["entry_count"] for r in results)
    total_saved = sum(r["estimated_saved_tokens"] for r in results)
    total_original = sum(r["estimated_original_tokens"] for r in results)
    pct = total_saved / max(1, total_original) * 100
    est_cost = total_saved / 1_000_000 * 3.0  # $3/M tokens

    # Build a compact per-type line.
    type_lines = ", ".join(
        f"{r['label']}:{r['entry_count']}e/{r['estimated_saved_tokens']:,}t"
        for r in results
    )

    return {
        "continue": True,
        "additionalContext": (
            f"[Stop] Session stats persisted to daily_stats table. "
            f"Today: {total_entries} entries, "
            f"~{total_saved:,} tokens saved ({pct:.0f}%), "
            f"~${est_cost:.4f} saved. "
            f"Breakdown: {type_lines}. "
            f"Run `daily_report.py` for a full report."
        ),
    }


def handle_session_start(event: dict) -> dict:
    """Handle SessionStart: check daily_stats for previous compression activity.

    On session start, query the daily_stats table for yesterday's summary
    and today's in-flight data so the agent can pick up where it left off.
    """
    # 1. Yesterday's consolidated stats (from daily_stats table).
    try:
        yesterday_summary = get_yesterday_stats_summary()
    except Exception:
        yesterday_summary = None

    if yesterday_summary:
        type_lines = ", ".join(
            f"{t['type']}:{t['entries']}e"
            for t in yesterday_summary.get("by_type", [])
        )
        yesterday_context = (
            f"[SessionStart] Yesterday ({yesterday_summary['date']}): "
            f"{yesterday_summary['total_entries']} entries, "
            f"~{yesterday_summary['estimated_saved_tokens']:,} tokens saved. "
            f"Per-type: {type_lines}. "
            f"Run `daily_report.py` or `daily_report.py --week` for details."
        )
        return {
            "continue": True,
            "additionalContext": yesterday_context,
        }

    # 2. Fallback: check if there's today's in-flight data in cold_entries.
    count, _ = _count_today_cold_entries()
    if count > 0:
        return {
            "continue": True,
            "additionalContext": (
                f"[SessionStart] {count} compressed entries from today "
                f"are already in the cold cache (not yet aggregated). "
                f"Use `list_cached` to browse or `retrieve_full_content` "
                f"to restore any entry."
            ),
        }

    return {"continue": True}


# ── Main dispatch ────────────────────────────────────────────────────────────


_EVENT_HANDLERS = {
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "PreCompact": handle_pre_compact,
    "Stop": handle_stop,
    "SessionStart": handle_session_start,
}

# Track the current date so we can detect day changes and auto-save the
# previous day's report.
_last_report_date: str | None = None


def main() -> None:
    """Read Hook JSON from stdin, dispatch to handler, write response to stdout.

    On any error the script returns ``{"continue": true}`` so that the Hook
    system does not block the agent — a failed compression hint is never worth
    interrupting the user's workflow.
    """
    global _last_report_date

    _diag_log("=== hook_compress.py invoked ===")

    try:
        raw = sys.stdin.read()
        _diag_log(f"stdin received, length={len(raw)}")
        if not raw.strip():
            _diag_log("empty stdin — returning pass-through")
            sys.stdout.write(json.dumps({"continue": True}))
            return
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as je:
            _diag_log(f"json.loads failed (len={len(raw)}, pos={je.pos}): {je}")
            # Large tool_output often contains unescaped quotes/backslashes.
            event = _parse_event_lenient(raw)
            _diag_log(f"lenient parse: hook_event_name={event.get('hook_event_name','')} "
                      f"tool_name={event.get('tool_name','')} "
                      f"tool_output_len={len(str(event.get('tool_output','')))}")
    except (json.JSONDecodeError, OSError) as e:
        _diag_log(f"stdin parse error: {e}")
        sys.stdout.write(json.dumps({"continue": True}))
        return

    # CodeBuddy uses "hook_event_name"; fall back to "event" for manual testing.
    event_type = event.get("hook_event_name") or event.get("event", "")
    _diag_log(f"event_type={event_type} tool_name={event.get('tool_name','')}")

    handler = _EVENT_HANDLERS.get(event_type)

    if handler is None:
        # Unknown event type — silently pass through.
        _diag_log(f"no handler for event={event_type}")
        sys.stdout.write(json.dumps({"continue": True}))
        return

    # Day-change detection: if we cross midnight, auto-save yesterday's report.
    try:
        today = sys.modules.get("datetime")
        if today is None:
            import datetime as dt
            today = dt
        today_str = today.date.today().isoformat()
        if (
            _last_report_date is not None
            and _last_report_date != today_str
        ):
            # Day changed — trigger a daily report save
            _auto_save_yesterday_report(_last_report_date)
        _last_report_date = today_str
    except Exception as ex:
        _diag_log(f"day-change error: {ex}")

    try:
        result = handler(event)
        _diag_log(f"handler OK, result keys={list(result.keys())}")
    except Exception as ex:
        # Never let a hook exception block the agent.
        _diag_log(f"handler ERROR: {type(ex).__name__}: {ex}")
        import traceback
        try:
            _diag_log(traceback.format_exc())
        except Exception:
            pass
        result = {"continue": True}

    # Wrap with hookSpecificOutput for Claude Code / Codex compatibility.
    # This is a no-op if result has no additionalContext or already has
    # hookSpecificOutput.  CodeBuddy ignores the nested key; Claude Code
    # and Codex ignore the top-level key → zero-conf multi-platform output.
    if "additionalContext" in result:
        result = _wrap_output(event_type, result)

    _diag_log("writing response to stdout")
    sys.stdout.write(json.dumps(result, ensure_ascii=False))


def _auto_save_yesterday_report(yesterday_date: str) -> None:
    """Silently persist yesterday's stats to daily_stats table.

    The daily_stats table is the canonical store; on-demand file export
    is handled by `daily_report.py --save`.
    """
    try:
        persist_daily_stats(target_date=yesterday_date)
    except Exception:
        pass


if __name__ == "__main__":
    main()
