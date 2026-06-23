"""
Context-aware content compressor — based on Headroom compression techniques.

Provides deterministic compression functions that can be called as a script
or imported as a module for use in CodeBuddy workflows.

Features:
  - 7 content type detectors and specialized compressors
  - CCR (Compress-Cache-Retrieve) with TTL expiration and LRU eviction
  - Session-level compression statistics with per-type breakdown
  - Memory-bounded cache with automatic cleanup

Usage as script:
    echo '{"type": "json", "content": "[...large array...]"}' | python compress.py
    python compress.py --type log --file build.log
    python compress.py --type code --file source.py

Usage as module:
    from compress import compress, ContentType, get_stats, clear_cache
    result = compress(content, ContentType.JSON)
    stats = get_stats()
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

MIN_TOKENS_TO_COMPRESS = 250
MIN_JSON_ITEMS = 5
MAX_LINT_PER_SEVERITY = 5
MAX_SEARCH_RESULTS = 10
MAX_LOG_LINES = 50
PROTECT_RECENT_MESSAGES = 6  # 3 turns × 2 (user + assistant)

# ── Tiered Storage Configuration ─────────────────────────────────────────────
# Three-tier storage: Hot (memory) → Cold (SQLite disk) → Evicted (gone).
# Data flows: new entries go to hot; hot overflow spills to cold;
# cold access promotes back to hot; TTL expiry removes from both.

# ── L1: Hot Store (in-memory LRU) ──────────────────────────────────────────

HOT_MAX_ENTRIES = 150           # Max entries in hot memory
HOT_MAX_BYTES = 30_000_000      # Max hot memory (30MB)
HOT_TTL_SECONDS = 900           # Hot TTL (15 minutes)
HOT_MAX_ENTRY_BYTES = 300_000   # Entries >300KB go directly to cold
HOT_CLEANUP_INTERVAL = 120      # Hot cleanup every 2 minutes
HOT_SPILL_BATCH = 15            # How many entries to spill to cold at once

# ── L2: Cold Store (SQLite disk) ───────────────────────────────────────────

COLD_TTL_SECONDS = 7200         # Cold TTL (2 hours)
COLD_CLEANUP_INTERVAL = 600     # Cold cleanup every 10 minutes
COLD_MAX_ENTRY_BYTES = 2_000_000  # Cold single entry max (2MB)
COLD_MAX_TOTAL_BYTES = 200_000_000  # Cold total disk max (200MB)

# ── Cross-process-safe workspace resolution ──────────────────────────────

def _resolve_workspace() -> str:
    """Resolve the skill root in a cross-process-safe way.

    Different processes (IDE main, Hook scripts, MCP server) may have
    different working directories.  This function normalises them to a
    single root so all processes share the same SQLite cold store.

    Works for both project-local and global skill installations:

    - **Project-local**: ``<project>/.codebuddy/skills/context-compressor/``
      → resolves to ``<project>``.
    - **Global**: ``~/.codebuddy/skills/context-compressor/``
      → resolves to ``~`` (user home).

    Priority (highest first):

    1. Script-relative navigation — ``__file__`` → up 4 levels from
       ``.../context-compressor/scripts/compress.py``.  Works for both
       project-local and global installations because both contain a
       ``.codebuddy`` marker directory.
    2. ``CODEBUDDY_PROJECT_DIR`` env var — set by the CodeBuddy IDE;
       used as a fallback when ``__file__`` is unavailable
       (e.g. embedded execution).
    3. OS-specific default — platform-dependent fallback:

       - **Windows**: ``USERPROFILE`` env (or CWD if absent).
       - **macOS**: ``HOME`` env (or CWD if absent).
       - **Linux**: ``HOME`` env (or CWD if absent).

    Returns an absolute path to the skill root (the directory containing
    ``.codebuddy``).
    """
    # Priority 1: Script-relative — works for BOTH project and global installs.
    #   Project: <project>/.codebuddy/skills/context-compressor/scripts/  →  up 4 = <project>
    #   Global:  ~/.codebuddy/skills/context-compressor/scripts/          →  up 4 = ~
    # Both have a .codebuddy marker directory.
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        for _ in range(4):
            d = os.path.dirname(d)
        if os.path.isdir(os.path.join(d, ".codebuddy")):
            return d
    except (NameError, OSError):
        pass

    # Priority 2: CODEBUDDY_PROJECT_DIR — IDE-provided project root.
    ws = os.environ.get("CODEBUDDY_PROJECT_DIR")
    if ws:
        ws = os.path.abspath(ws)
        if os.path.isdir(ws):
            return ws

    # Priority 3: OS-specific default → final fallback.
    if sys.platform.startswith("win32"):
        _default = os.environ.get("USERPROFILE") or os.getcwd()
    elif sys.platform.startswith("darwin"):
        _default = os.environ.get("HOME") or os.getcwd()
    else:  # Linux and others
        _default = os.environ.get("HOME") or os.getcwd()

    return os.path.abspath(_default)


# ── Cold DB path resolution (cross-process sharing) ─────────────────────
# Priority: 1) CCR_DB_PATH env  →  2) workspace-relative  →  3) PID-temp.
# Setting a shared path ensures the MCP server and Hook scripts use
# the same SQLite file for cold storage.
_COLD_DB_RESOLVED: str | None = None
_CCR_ENV = os.environ.get("CCR_DB_PATH")
if _CCR_ENV:
    _COLD_DB_RESOLVED = _CCR_ENV
else:
    _WS = _resolve_workspace()
    _SHARED = os.path.join(
        _WS, ".codebuddy", "skills", "context-compressor", "cache"
    )
    os.makedirs(_SHARED, exist_ok=True)
    _COLD_DB_RESOLVED = os.path.join(_SHARED, "ccr_shared_cold.db")

COLD_DB_DIR: str | None = _COLD_DB_RESOLVED  # shared by default
COLD_EVICT_BATCH = 50           # How many cold entries to evict when limit hit


# ═══════════════════════════════════════════════════════════════════════════════
# Data types
# ═══════════════════════════════════════════════════════════════════════════════


class ContentType(Enum):
    JSON_ARRAY = "json"
    CODE = "code"
    LINT = "lint"
    LOG = "log"
    SEARCH = "search"
    DIFF = "diff"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class CompressResult:
    """Result of a single compression operation."""

    content: str
    original_tokens: int
    compressed_tokens: int
    content_type: ContentType
    cache_key: str = ""
    truncated_items: int = 0

    @property
    def ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return self.compressed_tokens / self.original_tokens

    @property
    def saved_pct(self) -> float:
        return (1.0 - self.ratio) * 100

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens

    @property
    def ccr_marker(self) -> str:
        """Generate CCR retrieval marker."""
        if not self.cache_key:
            return ""
        return (
            f"\n\n[Compressed: {self.original_tokens} -> {self.compressed_tokens} tokens "
            f"({self.saved_pct:.0f}% saved) | key: {self.cache_key}]"
        )


@dataclass
class SessionStats:
    """Cumulative compression statistics for the current session."""

    total_compressions: int = 0
    total_original_tokens: int = 0
    total_compressed_tokens: int = 0
    total_truncated_items: int = 0
    session_start: float = field(default_factory=time.monotonic)
    cache_hits: int = 0
    cache_misses: int = 0
    # Hot tier stats
    cache_evictions: int = 0       # entries that couldn't spill (permanent loss)
    cache_expirations: int = 0     # hot entries that expired (spilled to cold first)
    cache_current_entries: int = 0
    cache_current_bytes: int = 0
    hot_hits: int = 0
    # Cold tier stats
    cold_entries: int = 0
    cold_bytes: int = 0
    cold_spills: int = 0
    cold_promotions: int = 0
    cold_retrievals: int = 0
    cold_hits: int = 0
    cold_expirations: int = 0
    cold_rejects: int = 0
    cold_evicts: int = 0
    cold_enabled: bool = False
    # Latency (cumulative, microseconds)
    get_latency_us: float = 0.0
    put_latency_us: float = 0.0
    cold_get_latency_us: float = 0.0
    cold_put_latency_us: float = 0.0
    per_type: dict[str, dict[str, int]] = field(default_factory=dict)
    compression_timeline: list[dict[str, Any]] = field(default_factory=list)

    def record(self, result: CompressResult) -> None:
        """Record a compression result."""
        self.total_compressions += 1
        self.total_original_tokens += result.original_tokens
        self.total_compressed_tokens += result.compressed_tokens
        self.total_truncated_items += result.truncated_items

        ctype = result.content_type.value
        if ctype not in self.per_type:
            self.per_type[ctype] = {"count": 0, "original": 0, "compressed": 0, "saved": 0}
        self.per_type[ctype]["count"] += 1
        self.per_type[ctype]["original"] += result.original_tokens
        self.per_type[ctype]["compressed"] += result.compressed_tokens
        self.per_type[ctype]["saved"] += result.tokens_saved

        # Keep last 50 timeline entries
        self.compression_timeline.append({
            "time": time.strftime("%H:%M:%S"),
            "type": ctype,
            "original": result.original_tokens,
            "compressed": result.compressed_tokens,
            "saved_pct": round(result.saved_pct, 1),
        })
        if len(self.compression_timeline) > 50:
            self.compression_timeline = self.compression_timeline[-50:]

    @property
    def total_saved(self) -> int:
        return self.total_original_tokens - self.total_compressed_tokens

    @property
    def overall_ratio(self) -> float:
        if self.total_original_tokens == 0:
            return 0.0
        return self.total_compressed_tokens / self.total_original_tokens

    @property
    def overall_saved_pct(self) -> float:
        return (1.0 - self.overall_ratio) * 100

    @property
    def session_duration_seconds(self) -> float:
        return time.monotonic() - self.session_start

    def summary(self) -> str:
        """Generate a human-readable summary report."""
        lines: list[str] = []
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + " [*] Context Compression Statistics".ljust(56) + "|")
        lines.append("+" + "-" * 58 + "+")

        # Session overview
        duration_mins = self.session_duration_seconds / 60
        lines.append(
            "|" +
            f" Session: {duration_mins:.0f}min  |  Compressions: {self.total_compressions}".ljust(56) +
            "|"
        )

        # Token summary
        saved = self.total_saved
        lines.append(
            "|" +
            f" Tokens: {self.total_original_tokens:>8,}  ->  {self.total_compressed_tokens:>8,}".ljust(56) +
            "|"
        )
        lines.append(
            "|" +
            f" SAVED: {saved:>8,} tokens  ({self.overall_saved_pct:.0f}%)".ljust(56) +
            "|"
        )

        # Cost estimate (assumed pricing)
        if saved > 0:
            # Claude Sonnet roughly $3 per M input tokens
            est_cost_saved = saved / 1_000_000 * 3.0
            lines.append(
                "|" +
                f" Est. cost saved: ~${est_cost_saved:.3f}".ljust(56) +
                "|"
            )

        # Per-type breakdown
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + " By Content Type:".ljust(56) + "|")

        for ctype, stats in sorted(
            self.per_type.items(),
            key=lambda x: x[1]["saved"],
            reverse=True,
        ):
            name_map = {
                "json": "JSON",
                "code": "Code",
                "lint": "Lint",
                "log": "Log",
                "search": "Search",
                "diff": "Diff",
                "text": "Text",
            }
            name = name_map.get(ctype, ctype)
            s = stats
            line = (
                f"  {name:<8} {s['count']:>3}x  "
                f"{s['saved']:>6,}t saved ({s['saved'] / max(1, s['original']) * 100:.0f}%)"
            )
            lines.append("|" + line.ljust(56) + "|")

        # Cache status — Tiered
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + " Cache (Tiered Storage):".ljust(56) + "|")

        # Hot tier
        hot_kb = self.cache_current_bytes / 1024
        hot_pct = self.cache_current_bytes / max(1, HOT_MAX_BYTES) * 100
        lines.append(
            "|" +
            f"  [Hot]  {self.cache_current_entries}/{HOT_MAX_ENTRIES} entries".ljust(36) +
            f"~{hot_kb:.0f}KB ({hot_pct:.0f}%)".ljust(20) +
            "|"
        )
        lines.append(
            "|" +
            f"  Hits: {self.cache_hits}  Hot: {self.hot_hits}  Miss: {self.cache_misses}".ljust(56) +
            "|"
        )
        # Latency
        if self.get_latency_us > 0:
            avg = self.get_latency_us / max(1, self.cache_hits + self.cache_misses)
            lines.append(
                "|" +
                f"  Get avg: {avg:.0f}μs  Put avg: {self.put_latency_us / max(1, self.cache_current_entries):.0f}μs".ljust(56) +
                "|"
            )

        # Cold tier
        if self.cold_enabled:
            cold_kb = self.cold_bytes / 1024
            cold_pct = self.cold_bytes / max(1, COLD_MAX_TOTAL_BYTES) * 100
            lines.append(
                "|" +
                f"  [Cold] {self.cold_entries} entries".ljust(30) +
                f"~{cold_kb:.0f}KB ({cold_pct:.0f}%) TTL:{COLD_TTL_SECONDS}s".ljust(26) +
                "|"
            )
            lines.append(
                "|" +
                f"  Spill: {self.cold_spills} Promote: {self.cold_promotions}".ljust(30) +
                f"Hit: {self.cold_hits} Evict: {self.cold_evicts}".ljust(26) +
                "|"
            )
            lines.append(
                "|" +
                f"  Cold get: {self.cold_retrievals} Exp: {self.cold_expirations} Rej: {self.cold_rejects}".ljust(56) +
                "|"
            )
        else:
            lines.append(
                "|" +
                "  [Cold] unavailable (SQLite init failed)".ljust(56) +
                "|"
            )

        # Recent activity
        if self.compression_timeline:
            lines.append("+" + "-" * 58 + "+")
            lines.append("|" + " Recent (last 5):".ljust(56) + "|")
            for entry in self.compression_timeline[-5:]:
                line = (
                    f"  {entry['time']}  {entry['type']:<8} "
                    f"{entry['original']:>4}->{entry['compressed']:<4}t "
                    f"(-{entry['saved_pct']:.0f}%)"
                )
                lines.append("|" + line.ljust(56) + "|")

        lines.append("+" + "-" * 58 + "+")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export stats as a dictionary for JSON serialization."""
        return {
            "total_compressions": self.total_compressions,
            "total_original_tokens": self.total_original_tokens,
            "total_compressed_tokens": self.total_compressed_tokens,
            "total_saved_tokens": self.total_saved,
            "overall_saved_pct": round(self.overall_saved_pct, 1),
            "session_duration_seconds": round(self.session_duration_seconds, 0),
            "per_type": self.per_type,
            "cache": {
                "hot": {
                    "current_entries": self.cache_current_entries,
                    "current_bytes": self.cache_current_bytes,
                    "max_entries": HOT_MAX_ENTRIES,
                    "max_bytes": HOT_MAX_BYTES,
                    "ttl_seconds": HOT_TTL_SECONDS,
                },
                "cold": {
                    "enabled": self.cold_enabled,
                    "current_entries": self.cold_entries,
                    "current_bytes": self.cold_bytes,
                    "max_bytes": COLD_MAX_TOTAL_BYTES,
                    "spills": self.cold_spills,
                    "promotions": self.cold_promotions,
                    "retrievals": self.cold_retrievals,
                    "expirations": self.cold_expirations,
                    "rejects": self.cold_rejects,
                    "size_evicts": self.cold_evicts,
                    "ttl_seconds": COLD_TTL_SECONDS,
                    "max_entry_bytes": COLD_MAX_ENTRY_BYTES,
                },
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hot_hits": self.hot_hits,
                "cold_hits": self.cold_hits,
                "evictions": self.cache_evictions,
                "expirations": self.cache_expirations,
                "latency_us": {
                    "get_total": round(self.get_latency_us, 0),
                    "put_total": round(self.put_latency_us, 0),
                    "cold_get_total": round(self.cold_get_latency_us, 0),
                    "cold_put_total": round(self.cold_put_latency_us, 0),
                },
            },
            "recent_compressions": self.compression_timeline[-10:],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Tiered Storage: L1 Hot (memory) + L2 Cold (SQLite) → L3 Evicted (gone)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class _CacheEntry:
    """A single cache entry with metadata for expiration and eviction."""

    key: str
    content: str
    stored_at: float          # monotonic timestamp
    size_bytes: int
    content_type: str


class _ColdStore:
    """L2 disk-based cold storage using SQLite.

    Design:
      - SQLite WAL + NORMAL sync for fast writes with crash safety.
      - Prepared statement cache for hot-path queries.
      - Indexed queries by key, timestamp, content_type.
      - Size-bounded: evicts least-retrieved entries when COLD_MAX_TOTAL_BYTES hit.
      - Longer TTL than hot store (2 hours vs 15 minutes).
      - Auto-creates database in temp directory per session.
      - Silent fallback: if DB init fails, hot-only mode continues.
    """

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS cold_entries (
            key         TEXT PRIMARY KEY,
            content     TEXT NOT NULL,
            content_type TEXT DEFAULT 'unknown',
            size_bytes   INTEGER DEFAULT 0,
            stored_at    REAL NOT NULL,
            retrieved_count INTEGER DEFAULT 0,
            last_retrieved_at REAL
        );
        CREATE INDEX IF NOT EXISTS idx_cold_stored_at ON cold_entries(stored_at);
        CREATE INDEX IF NOT EXISTS idx_cold_content_type ON cold_entries(content_type);
        CREATE INDEX IF NOT EXISTS idx_cold_retrieved ON cold_entries(retrieved_count);
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA cache_size=-8000;
        PRAGMA temp_store=MEMORY;
    """

    def __init__(self, db_path: str | None = None) -> None:
        import sqlite3
        import tempfile
        import os

        self._lock = threading.Lock()

        if db_path is None:
            db_dir = tempfile.gettempdir()
            pid = os.getpid()
            db_path = os.path.join(
                db_dir, f"_ccr_cold_{pid}_{int(time.time())}.db"
            )
        self._db_path = db_path
        self._enabled = False

        try:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(self._SCHEMA)
            self._enabled = True
        except Exception:
            # Fallback: operate in hot-only mode
            self._conn = None
            self._enabled = False

        self.spills: int = 0        # entries moved from hot to cold
        self.promotions: int = 0    # entries moved from cold to hot
        self.expirations: int = 0   # cold entries cleaned up
        self.retrievals: int = 0    # successful gets from cold
        self._last_cleanup: float = time.monotonic()
        self._rejects: int = 0      # entries too large even for cold
        self._cold_evicts: int = 0  # entries evicted due to cold size limit
        self.get_latency_us: float = 0.0  # cumulative get latency in microseconds
        self.put_latency_us: float = 0.0  # cumulative put latency in microseconds

    def put(self, key: str, content: str, content_type: str = "unknown") -> bool:
        """Store content in cold storage. Returns True on success."""
        if not self._enabled or self._conn is None:
            return False

        size = len(content.encode("utf-8"))
        if size > COLD_MAX_ENTRY_BYTES:
            self._rejects += 1
            return False

        with self._lock:
            try:
                t0 = time.monotonic()
                self._conn.execute(
                    "INSERT OR REPLACE INTO cold_entries "
                    "(key, content, content_type, size_bytes, stored_at, retrieved_count) "
                    "VALUES (?, ?, ?, ?, ?, 0)",
                    (key, content, content_type, size, time.monotonic()),
                )
                self._conn.commit()
                self.put_latency_us += (time.monotonic() - t0) * 1_000_000

                # Evict if disk usage exceeded (evict least-retrieved first)
                total = self._conn.execute(
                    "SELECT COALESCE(SUM(size_bytes), 0) FROM cold_entries"
                ).fetchone()[0]
                if total > COLD_MAX_TOTAL_BYTES:
                    self._evict_cold_entries()
                return True
            except Exception:
                return False

    def _evict_cold_entries(self) -> None:
        """Evict COLD_EVICT_BATCH least-retrieved entries to make room."""
        if self._conn is None:
            return
        try:
            cursor = self._conn.execute(
                "SELECT key, size_bytes FROM cold_entries "
                "ORDER BY retrieved_count ASC, stored_at ASC LIMIT ?",
                (COLD_EVICT_BATCH,),
            )
            victims = cursor.fetchall()
            for row in victims:
                self._conn.execute("DELETE FROM cold_entries WHERE key = ?", (row["key"],))
                self._cold_evicts += 1
            self._conn.commit()
        except Exception:
            pass

    def get(self, key: str) -> str | None:
        """Retrieve content from cold storage. Updates retrieval metadata."""
        if not self._enabled or self._conn is None:
            return None

        with self._lock:
            self._maybe_cleanup()
            try:
                t0 = time.monotonic()
                row = self._conn.execute(
                    "SELECT content, stored_at FROM cold_entries WHERE key = ?",
                    (key,),
                ).fetchone()
            except Exception:
                return None

            if row is None:
                self.get_latency_us += (time.monotonic() - t0) * 1_000_000
                return None

            # Check TTL
            age = time.monotonic() - row["stored_at"]
            if age > COLD_TTL_SECONDS:
                self.remove(key)
                self.expirations += 1
                self.get_latency_us += (time.monotonic() - t0) * 1_000_000
                return None

            # Update retrieval metadata
            self.retrievals += 1
            try:
                self._conn.execute(
                    "UPDATE cold_entries SET retrieved_count = retrieved_count + 1, "
                    "last_retrieved_at = ? WHERE key = ?",
                    (time.monotonic(), key),
                )
                self._conn.commit()
            except Exception:
                pass

            self.get_latency_us += (time.monotonic() - t0) * 1_000_000
            return row["content"]

    def contains(self, key: str) -> bool:
        """Check if key exists in cold storage (fast lookup)."""
        if not self._enabled or self._conn is None:
            return False
        with self._lock:
            try:
                row = self._conn.execute(
                    "SELECT 1 FROM cold_entries WHERE key = ?", (key,)
                ).fetchone()
                return row is not None
            except Exception:
                return False

    def remove(self, key: str) -> bool:
        """Remove an entry from cold storage."""
        if not self._enabled or self._conn is None:
            return False
        with self._lock:
            try:
                cursor = self._conn.execute(
                    "DELETE FROM cold_entries WHERE key = ?", (key,)
                )
                self._conn.commit()
                return cursor.rowcount > 0
            except Exception:
                return False

    def clear(self) -> int:
        """Clear all cold entries. Returns count of removed entries."""
        if not self._enabled or self._conn is None:
            return 0
        with self._lock:
            try:
                count = self._conn.execute(
                    "SELECT COUNT(*) FROM cold_entries"
                ).fetchone()[0]
                self._conn.execute("DELETE FROM cold_entries")
                self._conn.commit()
                self._last_cleanup = time.monotonic()
                return count
            except Exception:
                return 0

    def list_keys(self, max_keys: int = 50) -> list[dict[str, Any]]:
        """List cold entries with metadata."""
        if not self._enabled or self._conn is None:
            return []
        with self._lock:
            self._maybe_cleanup()
            try:
                rows = self._conn.execute(
                    "SELECT key, size_bytes, stored_at, content_type, retrieved_count "
                    "FROM cold_entries ORDER BY stored_at DESC LIMIT ?",
                    (max_keys,),
                ).fetchall()
            except Exception:
                return []

            result = []
            for row in rows:
                age = time.monotonic() - row["stored_at"]
                result.append({
                    "key": row["key"],
                    "size_bytes": row["size_bytes"],
                    "age_seconds": round(age, 0),
                    "expires_in_seconds": round(max(0, COLD_TTL_SECONDS - age), 0),
                    "content_type": row["content_type"],
                    "retrieved_count": row["retrieved_count"],
                    "tier": "cold",
                })
            return result

    def query_by_type(self, content_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """Query cold entries by content type (for analysis)."""
        if not self._enabled or self._conn is None:
            return []
        with self._lock:
            try:
                rows = self._conn.execute(
                    "SELECT key, size_bytes, stored_at FROM cold_entries "
                    "WHERE content_type = ? ORDER BY stored_at DESC LIMIT ?",
                    (content_type, limit),
                ).fetchall()
            except Exception:
                return []
            return [dict(r) for r in rows]

    @property
    def entry_count(self) -> int:
        if not self._enabled or self._conn is None:
            return 0
        with self._lock:
            try:
                return self._conn.execute(
                    "SELECT COUNT(*) FROM cold_entries"
                ).fetchone()[0]
            except Exception:
                return 0

    @property
    def total_bytes(self) -> int:
        if not self._enabled or self._conn is None:
            return 0
        with self._lock:
            try:
                result = self._conn.execute(
                    "SELECT COALESCE(SUM(size_bytes), 0) FROM cold_entries"
                ).fetchone()[0]
                return result
            except Exception:
                return 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _maybe_cleanup(self) -> None:
        """Periodic sweep of expired cold entries."""
        if not self._enabled or self._conn is None:
            return
        now = time.monotonic()
        if now - self._last_cleanup < COLD_CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        try:
            cutoff = now - COLD_TTL_SECONDS
            cursor = self._conn.execute(
                "DELETE FROM cold_entries WHERE stored_at < ?", (cutoff,)
            )
            removed = cursor.rowcount
            self._conn.commit()
            self.expirations += removed
        except Exception:
            pass


class _TieredCache:
    """Three-tier CCR cache: Hot (L1/memory) + Cold (L2/SQLite) → Evicted (L3/gone).

    Lifecycle:
      put() → always stores in hot; batch-spills old entries to cold if hot is full.
              Entries exceeding HOT_MAX_ENTRY_BYTES go directly to cold.
      get() → checks hot first, then cold; promotes cold hits to hot.
      TTL  → hot entries expire after HOT_TTL_SECONDS (spilled to cold first).
              cold entries expire after COLD_TTL_SECONDS (removed permanently).
      Evict → cold evicts least-retrieved entries when COLD_MAX_TOTAL_BYTES hit.
    """

    def __init__(self) -> None:
        self._hot: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._hot_lock = threading.Lock()
        self._hot_bytes: int = 0
        self._hot_last_cleanup: float = time.monotonic()

        self._cold = _ColdStore(db_path=COLD_DB_DIR)

        # Aggregate stats
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0        # entries that couldn't spill (permanent loss)
        self.expirations: int = 0      # hot entries expired → spilled to cold
        # Per-tier hit stats
        self.hot_hits: int = 0
        self.cold_hits: int = 0
        # Latency tracking
        self.get_latency_us: float = 0.0
        self.put_latency_us: float = 0.0

    # ── Put ──────────────────────────────────────────────────────────────────

    def put(self, key: str, content: str, content_type: str = "unknown") -> bool:
        """Store content using tiered strategy. Returns True if stored anywhere."""
        t0 = time.monotonic()
        size = len(content.encode("utf-8"))

        # Oversized even for cold → refuse (count as cold reject)
        if size > COLD_MAX_ENTRY_BYTES:
            self._cold._rejects += 1
            self.put_latency_us += (time.monotonic() - t0) * 1_000_000
            return False

        # Too large for hot → go directly to cold
        if size > HOT_MAX_ENTRY_BYTES:
            result = self._cold.put(key, content, content_type)
            self.put_latency_us += (time.monotonic() - t0) * 1_000_000
            return result

        # Normal path: store in hot, batch-spill if needed
        with self._hot_lock:
            self._hot_cleanup()

            # Remove old entry if updating
            if key in self._hot:
                old = self._hot.pop(key)
                self._hot_bytes -= old.size_bytes

            # Batch spill: spill HOT_SPILL_BATCH entries to cold at once
            self._batch_spill_to_fit(size)

            entry = _CacheEntry(
                key=key,
                content=content,
                stored_at=time.monotonic(),
                size_bytes=size,
                content_type=content_type,
            )
            self._hot[key] = entry
            self._hot_bytes += size
            self.put_latency_us += (time.monotonic() - t0) * 1_000_000
            return True

    # ── Get ──────────────────────────────────────────────────────────────────

    def get(self, key: str) -> str | None:
        """Retrieve content: hot first, then cold (with promotion)."""
        t0 = time.monotonic()
        # 1. Check hot
        with self._hot_lock:
            self._hot_cleanup()

            if key in self._hot:
                entry = self._hot[key]
                age = time.monotonic() - entry.stored_at
                if age > HOT_TTL_SECONDS:
                    # Expired: spill to cold before removing
                    self._spill_entry_with_track(key, entry)
                    self.expirations += 1
                else:
                    self._hot.move_to_end(key)
                    self.hits += 1
                    self.hot_hits += 1
                    self.get_latency_us += (time.monotonic() - t0) * 1_000_000
                    return entry.content

        # 2. Check cold
        content = self._cold.get(key)
        if content is not None:
            self.hits += 1
            self.cold_hits += 1
            # Promote to hot (try; if too large, stays in cold only)
            size = len(content.encode("utf-8"))
            if size <= HOT_MAX_ENTRY_BYTES:
                with self._hot_lock:
                    self._batch_spill_to_fit(size)
                    self._hot[key] = _CacheEntry(
                        key=key,
                        content=content,
                        stored_at=time.monotonic(),
                        size_bytes=size,
                        content_type="unknown",
                    )
                    self._hot_bytes += size
                    self._cold.promotions += 1
                self._cold.remove(key)  # Remove from cold after promote
            self.get_latency_us += (time.monotonic() - t0) * 1_000_000
            return content

        self.misses += 1
        self.get_latency_us += (time.monotonic() - t0) * 1_000_000
        return None

    # ── Manage ───────────────────────────────────────────────────────────────

    def remove(self, key: str) -> bool:
        """Remove from both tiers."""
        removed = False
        with self._hot_lock:
            if key in self._hot:
                entry = self._hot.pop(key)
                self._hot_bytes -= entry.size_bytes
                removed = True
        if self._cold.remove(key):
            removed = True
        return removed

    def clear(self) -> int:
        """Clear both tiers. Returns total entries removed."""
        with self._hot_lock:
            hot_count = len(self._hot)
            self._hot.clear()
            self._hot_bytes = 0
            self._hot_last_cleanup = time.monotonic()
        cold_count = self._cold.clear()
        return hot_count + cold_count

    def list_keys(self, max_keys: int = 50) -> list[dict[str, Any]]:
        """List entries from both tiers with metadata."""
        result: list[dict[str, Any]] = []

        # Hot entries
        with self._hot_lock:
            self._hot_cleanup()
            now = time.monotonic()
            for key, entry in list(self._hot.items()):
                result.append({
                    "key": key,
                    "size_bytes": entry.size_bytes,
                    "age_seconds": round(now - entry.stored_at, 0),
                    "expires_in_seconds": round(
                        max(0, HOT_TTL_SECONDS - (now - entry.stored_at)), 0
                    ),
                    "content_type": entry.content_type,
                    "tier": "hot",
                })

        # Cold entries
        result.extend(self._cold.list_keys(max_keys))

        # Sort by most recently stored, limit
        result.sort(key=lambda x: x.get("age_seconds", 0))
        return result[:max_keys]

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def entry_count(self) -> int:
        with self._hot_lock:
            return len(self._hot) + self._cold.entry_count

    @property
    def total_bytes(self) -> int:
        with self._hot_lock:
            return self._hot_bytes + self._cold.total_bytes

    @property
    def hot_count(self) -> int:
        with self._hot_lock:
            return len(self._hot)

    @property
    def hot_bytes(self) -> int:
        with self._hot_lock:
            return self._hot_bytes

    @property
    def cold_count(self) -> int:
        return self._cold.entry_count

    @property
    def cold_bytes(self) -> int:
        return self._cold.total_bytes

    @property
    def cold_enabled(self) -> bool:
        return self._cold.enabled

    @property
    def cold_spills(self) -> int:
        return self._cold.spills

    @property
    def cold_promotions(self) -> int:
        return self._cold.promotions

    @property
    def cold_retrievals(self) -> int:
        return self._cold.retrievals

    @property
    def cold_rejects(self) -> int:
        return self._cold._rejects

    @property
    def cold_evicts(self) -> int:
        return self._cold._cold_evicts

    @property
    def cold_get_latency_us(self) -> float:
        return self._cold.get_latency_us

    @property
    def cold_put_latency_us(self) -> float:
        return self._cold.put_latency_us

    @property
    def hot_hit_rate(self) -> float:
        total = self.hot_hits + self.misses
        return self.hot_hits / max(1, total)

    @property
    def cold_hit_rate(self) -> float:
        """Cold hit rate = cold_hits / (cold_hits + misses)."""
        return self.cold_hits / max(1, self.cold_hits + self.misses)

    def cold_query_by_type(self, content_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """Query cold entries by content type."""
        return self._cold.query_by_type(content_type, limit)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _batch_spill_to_fit(self, needed_bytes: int) -> None:
        """Batch-spill up to HOT_SPILL_BATCH hot entries to cold.

        Instead of spilling one at a time (N SQLite commits), we batch the
        eligible entries and write them in a single flight, then commit once.
        """
        need_spill = (
            len(self._hot) >= HOT_MAX_ENTRIES
            or self._hot_bytes + needed_bytes > HOT_MAX_BYTES
        )
        if not need_spill or not self._hot:
            return

        # Collect victims (LRU order — first N entries in OrderedDict)
        victim_keys: list[str] = []
        for key in self._hot:
            victim_keys.append(key)
            if len(victim_keys) >= HOT_SPILL_BATCH:
                break

        # Batch-write to cold, then remove from hot
        spilled = 0
        for key in victim_keys:
            if key not in self._hot:  # Safety: may have been removed
                continue
            entry = self._hot[key]
            stored = self._cold.put(key, entry.content, entry.content_type)
            if stored:
                self._cold.spills += 1
                spilled += 1
            else:
                self.evictions += 1
            del self._hot[key]
            self._hot_bytes -= entry.size_bytes

    def _spill_entry_with_track(self, key: str, entry: _CacheEntry) -> None:
        """Spill a specific hot entry to cold (used for TTL expiry)."""
        if key in self._hot:
            del self._hot[key]
            self._hot_bytes -= entry.size_bytes
        stored = self._cold.put(key, entry.content, entry.content_type)
        if stored:
            self._cold.spills += 1
        else:
            self.evictions += 1

    def _hot_cleanup(self) -> None:
        """Periodic cleanup of expired hot entries (spills to cold first)."""
        now = time.monotonic()
        if now - self._hot_last_cleanup < HOT_CLEANUP_INTERVAL:
            return
        self._hot_last_cleanup = now

        expired = []
        for key, entry in self._hot.items():
            if now - entry.stored_at > HOT_TTL_SECONDS:
                expired.append((key, entry))

        for key, entry in expired:
            self._spill_entry_with_track(key, entry)
            self.expirations += 1


# ── Global instances ─────────────────────────────────────────────────────────

_cache = _TieredCache()
_stats = SessionStats()


# ═══════════════════════════════════════════════════════════════════════════════
# Detector
# ═══════════════════════════════════════════════════════════════════════════════


def estimate_tokens(content: str) -> int:
    """Rough token estimation: ~4 chars per token (conservative).

    For CJK text, each character is typically 1-2 tokens, while Latin text
    averages ~4 chars per token. Using 4 as a baseline is slightly conservative.
    """
    return max(1, len(content) // 4)


_ERROR_PATTERN = re.compile(
    r"(error|ERROR|Error|ERR|fatal|Fatal|panic|PANIC|exception|traceback)",
)
_WARNING_PATTERN = re.compile(r"(warning|WARNING|warn|WARN|deprecated)")


def detect_content_type(content: str) -> ContentType:
    """Detect content type by analyzing content structure and keywords.

    Uses the same structural-first approach as Headroom's ContentRouter,
    but with regex-based fallbacks instead of ML (simplified for portability).
    """
    content_stripped = content.strip()

    # Try JSON first (headroom's SmartCrusher handles this)
    if content_stripped.startswith("[") or content_stripped.startswith("{"):
        try:
            json.loads(content_stripped)
            if content_stripped.startswith("["):
                return ContentType.JSON_ARRAY
            return ContentType.UNKNOWN  # JSON object, not array
        except (json.JSONDecodeError, ValueError):
            pass

    # Git diff
    if content_stripped.startswith("diff --git") or content_stripped.startswith(
        "diff --"
    ):
        return ContentType.DIFF

    # Structural detectors first (more reliable than keyword-based)
    lines = content_stripped.splitlines()
    sample = lines[:20]  # Check first 20 lines

    # Lint output (filename:line:column: message) — structural, high priority
    lint_pattern = re.compile(r"^[^\s]+\.[a-zA-Z]+:\d+:\d*:?\s")
    if any(lint_pattern.match(line) for line in sample):
        return ContentType.LINT

    # Search/grep results (file:line:content) — structural
    search_pattern = re.compile(r"^[^\s]+\.[a-zA-Z]+:\d+:")
    match_count = sum(1 for line in sample if search_pattern.match(line))
    if match_count >= 3:
        return ContentType.SEARCH

    # Build/test log patterns (timestamp prefixes, compilation output) — keyword-based
    log_indicators = 0
    for line in sample:
        if re.search(r"\d{2}:\d{2}:\d{2}", line):
            log_indicators += 1
        if _ERROR_PATTERN.search(line):
            log_indicators += 2
        if _WARNING_PATTERN.search(line):
            log_indicators += 1
    if log_indicators >= 3:
        return ContentType.LOG

    # Code (function/class definitions)
    code_indicators = sum(
        1
        for line in sample
        if any(
            kw in line
            for kw in [
                "func ",
                "def ",
                "class ",
                "function ",
                "import ",
                "from ",
                "package ",
                "struct ",
                "type ",
                "const ",
                "var ",
                "let ",
                "fn ",
                "pub ",
                "export ",
                "interface ",
            ]
        )
    )
    if code_indicators >= 3:
        return ContentType.CODE

    return ContentType.TEXT


# ═══════════════════════════════════════════════════════════════════════════════
# Compressors
# ═══════════════════════════════════════════════════════════════════════════════


def compress_json_array(content: str) -> CompressResult:
    """SmartCrusher-like JSON array compression.

    Strategies:
    - Arrays < MIN_JSON_ITEMS items: return as-is
    - Keep first 3 + last 2 items for range understanding
    - Keep anomaly items (errors, exceptions, nulls, outliers)
    - Dedup similar items (keep one representative)
    - Summarize dropped items with count
    """
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return CompressResult(
            content=content,
            original_tokens=estimate_tokens(content),
            compressed_tokens=estimate_tokens(content),
            content_type=ContentType.JSON_ARRAY,
        )

    if not isinstance(data, list):
        return CompressResult(
            content=content,
            original_tokens=estimate_tokens(content),
            compressed_tokens=estimate_tokens(content),
            content_type=ContentType.JSON_ARRAY,
        )

    original_count = len(data)
    original_tokens = estimate_tokens(content)

    if original_count <= MIN_JSON_ITEMS:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.JSON_ARRAY,
        )

    kept: list[dict[str, Any]] = []

    # 1. Keep first 3 items (head context)
    for item in data[:min(3, original_count)]:
        if isinstance(item, dict):
            kept.append(item)

    # 2. Keep last 2 items (tail context)
    if original_count > 3:
        for item in data[-min(2, original_count - 3):]:
            if isinstance(item, dict) and item not in kept:
                kept.append(item)

    # 3. Find anomalies (errors, exceptions, empty values)
    anomaly_key_names = {"error", "Error", "ERROR", "exception", "Exception"}
    anomaly_level_values = {"error", "fatal", "critical", "err", "panic"}
    middle = data[3 : -2] if original_count > 5 else []
    anomalies = []
    for item in middle:
        if isinstance(item, dict):
            is_anomaly = False
            for key, val in item.items():
                if key in anomaly_key_names:
                    is_anomaly = True
                    break
                if isinstance(val, str) and val.lower() in anomaly_level_values:
                    is_anomaly = True
                    break
            if is_anomaly:
                anomalies.append(item)
    kept_anomaly_keys = set()
    for a in anomalies:
        key = json.dumps(a, sort_keys=True, default=str)
        if key not in kept_anomaly_keys:
            kept_anomaly_keys.add(key)
            kept.append(a)
            if len(kept) >= 20:
                break

    dropped = original_count - len(kept)
    kept_content = json.dumps(kept, indent=2, ensure_ascii=False, default=str)
    summary = f"\n// [{dropped} similar items omitted — {original_count} total records]"

    result_content = kept_content + summary
    compressed_tokens = estimate_tokens(result_content)

    return CompressResult(
        content=result_content,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        content_type=ContentType.JSON_ARRAY,
        truncated_items=dropped,
    )


def compress_lint(content: str) -> CompressResult:
    """Compress lint/diagnostic output.

    Groups by severity, keeps top N per group.
    """
    original_tokens = estimate_tokens(content)
    lines = content.strip().splitlines()

    errors = []
    warnings = []
    infos = []
    others = []

    for line in lines:
        line_lower = line.lower()
        if "error" in line_lower:
            errors.append(line)
        elif "warning" in line_lower or "warn" in line_lower:
            warnings.append(line)
        elif "info" in line_lower or "hint" in line_lower or "note" in line_lower:
            infos.append(line)
        else:
            others.append(line)

    result_lines = []

    if errors:
        result_lines.append(f"### ERROR ({len(errors)} 条):")
        result_lines.extend(f"  {e}" for e in errors[:MAX_LINT_PER_SEVERITY])
        if len(errors) > MAX_LINT_PER_SEVERITY:
            result_lines.append(f"  ... 还有 {len(errors) - MAX_LINT_PER_SEVERITY} 条 error")
        result_lines.append("")

    if warnings:
        result_lines.append(f"### WARNING ({len(warnings)} 条):")
        result_lines.extend(f"  {w}" for w in warnings[:MAX_LINT_PER_SEVERITY])
        if len(warnings) > MAX_LINT_PER_SEVERITY:
            result_lines.append(f"  ... 还有 {len(warnings) - MAX_LINT_PER_SEVERITY} 条 warning")
        result_lines.append("")

    if infos:
        result_lines.append(f"### INFO/HINT ({len(infos)} 条，已折叠):")
        result_lines.append(f"  {len(infos)} 条提示信息已折叠")

    if others:
        result_lines.append(f"### 其他 ({len(others)} 条，已折叠):")
        result_lines.append(f"  {len(others)} 条未分类信息已折叠")

    result = "\n".join(result_lines)
    truncated = len(lines) - (
        len(errors[:MAX_LINT_PER_SEVERITY]) + len(warnings[:MAX_LINT_PER_SEVERITY])
    )
    return CompressResult(
        content=result,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result),
        content_type=ContentType.LINT,
        truncated_items=max(0, truncated),
    )


def compress_log(content: str) -> CompressResult:
    """Compress log output.

    Keeps ERROR/FATAL lines, samples WARNING lines, collapses repetitive INFO lines.
    Headroom-inspired approach: high-priority lines preserved, dilution removed.
    """
    original_tokens = estimate_tokens(content)
    lines = content.strip().splitlines()

    if len(lines) <= MAX_LOG_LINES:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.LOG,
        )

    errors = [l for l in lines if _ERROR_PATTERN.search(l)]
    warnings = [l for l in lines if _WARNING_PATTERN.search(l)]
    others = [l for l in lines if not _ERROR_PATTERN.search(l) and not _WARNING_PATTERN.search(l)]

    result_lines = []

    if errors:
        result_lines.append(f"### ERROR/FATAL ({len(errors)} 行):")
        result_lines.extend(f"  {e}" for e in errors[:15])
        if len(errors) > 15:
            result_lines.append(f"  ... 还有 {len(errors) - 15} 行 error")
        result_lines.append("")

    if warnings:
        sample = min(len(warnings), 10)
        result_lines.append(f"### WARNING ({len(warnings)} 行, 展示 {sample} 行):")
        step = max(1, len(warnings) // sample) if sample > 0 else 1
        result_lines.extend(f"  {warnings[i]}" for i in range(0, len(warnings), step)[:sample])
        result_lines.append("")

    if others:
        result_lines.append(f"### 其他 ({len(others)} 行, 已折叠):")
        result_lines.extend(f"  {others[i]}" for i in range(min(3, len(others))))
        if len(others) > 6:
            result_lines.append(f"  ... ({len(others) - 5} 行已折叠) ...")
        result_lines.extend(f"  {others[i]}" for i in range(max(3, len(others) - 2), len(others)))

    result = "\n".join(result_lines)
    return CompressResult(
        content=result,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result),
        content_type=ContentType.LOG,
        truncated_items=len(lines) - (len(errors[:15]) + min(len(warnings), 10) + 5),
    )


def compress_search(content: str) -> CompressResult:
    """Compress search/grep results.

    Groups by file, keeps top matches per file.
    """
    original_tokens = estimate_tokens(content)
    lines = content.strip().splitlines()

    if len(lines) <= MAX_SEARCH_RESULTS:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.SEARCH,
        )

    file_groups: dict[str, list[str]] = {}
    search_pattern = re.compile(r"^([^:]+):\d+:")

    for line in lines:
        m = search_pattern.match(line)
        if m:
            file_name = m.group(1)
            file_groups.setdefault(file_name, []).append(line)
        else:
            file_groups.setdefault("(raw)", []).append(line)

    result_lines = [f"## 搜索结果 (共 {len(lines)} 条, {len(file_groups)} 个文件)\n"]

    for file_name, file_lines in sorted(file_groups.items(), key=lambda x: -len(x[1])):
        result_lines.append(f"### {file_name} ({len(file_lines)} 条匹配):")
        result_lines.extend(f"  {l}" for l in file_lines[:5])
        if len(file_lines) > 5:
            result_lines.append(f"  ... 还有 {len(file_lines) - 5} 条匹配")
        result_lines.append("")

    result = "\n".join(result_lines)
    return CompressResult(
        content=result,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result),
        content_type=ContentType.SEARCH,
        truncated_items=len(lines) - sum(min(len(fl), 5) for fl in file_groups.values()),
    )


def compress_code(content: str) -> CompressResult:
    """Compress code files by preserving function signatures and folding bodies.

    Simplified version of Headroom's CodeCompressor (no tree-sitter dependency).
    Preserves: function signatures, class definitions, import statements, comments.
    Folds: function bodies with placeholder.
    """
    original_tokens = estimate_tokens(content)
    lines = content.splitlines()

    if len(lines) <= 100:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.CODE,
        )

    func_patterns = re.compile(
        r"^\s*(def |class |func |function |async def |async function |"
        r"pub fn |fn |public |private |protected |"
        r"export (const |function |class |default )?|"
        r"import |from |package |use |module )"
    )

    result_lines = []
    in_function = False
    func_lines_count = 0
    folded_count = 0

    for line in lines:
        stripped = line.rstrip()

        if func_patterns.match(line) and not in_function and not stripped.endswith(";"):
            if in_function:
                if func_lines_count > 10:
                    result_lines.append(f"    // ... {func_lines_count - 5} lines folded")
                    folded_count += 1
                in_function = False

            result_lines.append(line)
            if stripped.endswith("{") or stripped.endswith(":"):
                in_function = True
                func_lines_count = 0
            continue

        if in_function:
            func_lines_count += 1
            if func_lines_count <= 3:
                result_lines.append(line)
            if stripped.rstrip() in {"}", "end", ");"} or (
                stripped and not stripped[0].isspace() and func_lines_count > 3
            ):
                if func_lines_count > 3:
                    result_lines.append(f"    // ... {func_lines_count - 3} lines folded")
                    folded_count += 1
                if stripped.rstrip() in {"}", "end", ");"}:
                    result_lines.append(line)
                in_function = False
            continue

        result_lines.append(line)

    if in_function and func_lines_count > 3:
        result_lines.append(f"    // ... {func_lines_count - 3} lines folded")
        folded_count += 1

    result_content = "\n".join(result_lines)
    result_content += f"\n\n// [{folded_count} function bodies folded — original {len(lines)} lines]"

    return CompressResult(
        content=result_content,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result_content),
        content_type=ContentType.CODE,
        truncated_items=folded_count,
    )


def compress_diff(content: str) -> CompressResult:
    """Compress git diff output.

    Headroom-inspired: discard lockfile diffs, whitespace-only hunks.
    """
    original_tokens = estimate_tokens(content)
    lines = content.splitlines()

    if len(lines) <= 50:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.DIFF,
        )

    lockfile_suffixes = {
        "Cargo.lock", "package-lock.json", "yarn.lock",
        "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
        "Gemfile.lock", "go.sum", "composer.lock",
    }

    result_lines = []
    in_lockfile = False
    dropped_hunks = 0

    for line in lines:
        if line.startswith("diff --git "):
            parts = line.split()
            file_path = parts[-1] if parts else ""
            in_lockfile = any(file_path.endswith(suffix) for suffix in lockfile_suffixes)

        if not in_lockfile:
            result_lines.append(line)
        else:
            dropped_hunks += 1

    result = "\n".join(result_lines)
    if dropped_hunks:
        result += f"\n// [{dropped_hunks} lockfile diff lines omitted]"

    return CompressResult(
        content=result,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result),
        content_type=ContentType.DIFF,
        truncated_items=dropped_hunks,
    )


def compress_text(content: str) -> CompressResult:
    """Compress free-form text.

    Keeps first 25% and last 15% of content as context windows.
    """
    original_tokens = estimate_tokens(content)
    lines = content.splitlines()

    if len(lines) <= 30:
        return CompressResult(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            content_type=ContentType.TEXT,
        )

    head_count = max(5, len(lines) // 4)
    tail_count = max(3, len(lines) // 7)

    result_lines = lines[:head_count]
    skipped = len(lines) - head_count - tail_count
    if skipped > 0:
        result_lines.append(f"\n... [{skipped} lines omitted] ...\n")
    result_lines.extend(lines[-tail_count:])

    result = "\n".join(result_lines)
    return CompressResult(
        content=result,
        original_tokens=original_tokens,
        compressed_tokens=estimate_tokens(result),
        content_type=ContentType.TEXT,
        truncated_items=skipped,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════


def compress(
    content: str,
    content_type: ContentType | None = None,
    store: bool = True,
) -> CompressResult:
    """Main compression entry point — Headroom-style content routing.

    Args:
        content: The content to compress.
        content_type: Optional type hint. If None, auto-detects.
        store: Whether to cache the original in CCR store (default True).

    Returns:
        CompressResult with compressed content and metrics.
    """
    # Threshold check
    tokens = estimate_tokens(content)
    if tokens < MIN_TOKENS_TO_COMPRESS:
        return CompressResult(
            content=content,
            original_tokens=tokens,
            compressed_tokens=tokens,
            content_type=content_type or ContentType.UNKNOWN,
        )

    # Detect or use hint
    if content_type is None:
        content_type = detect_content_type(content)

    # Route to compressor
    compressor_map = {
        ContentType.JSON_ARRAY: compress_json_array,
        ContentType.LINT: compress_lint,
        ContentType.LOG: compress_log,
        ContentType.SEARCH: compress_search,
        ContentType.CODE: compress_code,
        ContentType.DIFF: compress_diff,
        ContentType.TEXT: compress_text,
    }

    compressor = compressor_map.get(content_type, compress_text)
    result = compressor(content)

    # Generate cache key for CCR (surrogate-safe: replace invalid chars).
    cache_key = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:12]
    result.cache_key = cache_key

    # Store original for retrieval (if compressed)
    if store and result.tokens_saved > 0:
        _cache.put(cache_key, content, content_type=content_type.value)

    # Record stats
    _stats.record(result)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Public Cache API
# ═══════════════════════════════════════════════════════════════════════════════


def store_original(content: str, content_type: str = "unknown") -> str:
    """Store original content for CCR retrieval. Returns cache key.

    Stores through the two-tier cache (hot → cold, with TTL).  The hot tier
    is in-process memory, so it does not survive process boundaries.  For
    cross-process persistence (e.g. from a Hook script), use
    :func:`persist_to_cold` instead.
    """
    cache_key = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:12]
    _cache.put(cache_key, content, content_type=content_type)
    return cache_key


def persist_to_cold(content: str, content_type: str = "unknown") -> str:
    """Store content **directly** to the cold (SQLite) tier, bypassing hot.

    This is intended for short-lived processes (Hook scripts, one-shot
    utilities) where the in-memory hot cache would be lost on exit.
    The cold store uses a workspace-relative database path so that the
    MCP server and Hook scripts share the same persistent storage.

    Returns the cache key (a 12-char hex string) that can be used with
    :func:`retrieve_original` from any process sharing the workspace.
    """
    cache_key = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:12]

    # Workspace-relative path for cross-process sharing.
    workspace = _resolve_workspace()
    db_dir = os.path.join(
        workspace, ".codebuddy", "skills", "context-compressor", "cache"
    )
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "ccr_shared_cold.db")

    store = _ColdStore(db_path=db_path)
    store.put(cache_key, content, content_type=content_type)

    return cache_key


def retrieve_original(cache_key: str) -> str | None:
    """Retrieve original content by cache key. Returns None if not found or expired."""
    return _cache.get(cache_key)


def clear_cache() -> dict[str, Any]:
    """Clear all cached entries. Returns cleanup summary."""
    count = _cache.clear()
    return {
        "removed_entries": count,
        "cache_status": "cleared",
    }


def list_cached_entries(max_keys: int = 50) -> list[dict[str, Any]]:
    """List cached entries from both tiers with metadata."""
    return _cache.list_keys(max_keys)


def get_tier_summary() -> dict[str, Any]:
    """Get a summary of the tiered storage breakdown."""
    return {
        "hot": {
            "entries": _cache.hot_count,
            "bytes": _cache.hot_bytes,
            "max_entries": HOT_MAX_ENTRIES,
            "max_bytes": HOT_MAX_BYTES,
            "ttl_seconds": HOT_TTL_SECONDS,
            "hits": _cache.hot_hits,
        },
        "cold": {
            "enabled": _cache.cold_enabled,
            "entries": _cache.cold_count,
            "bytes": _cache.cold_bytes,
            "max_bytes": COLD_MAX_TOTAL_BYTES,
            "spills": _cache.cold_spills,
            "promotions": _cache.cold_promotions,
            "retrievals": _cache.cold_retrievals,
            "rejects": _cache.cold_rejects,
            "size_evicts": _cache.cold_evicts,
            "ttl_seconds": COLD_TTL_SECONDS,
        },
        "total": {
            "entries": _cache.entry_count,
            "bytes": _cache.total_bytes,
        },
        "hit_rates": {
            "hits": _cache.hits,
            "misses": _cache.misses,
            "hot_hits": _cache.hot_hits,
            "cold_hits": _cache.cold_hits,
        },
        "latency_us": {
            "get_total": round(_cache.get_latency_us, 0),
            "put_total": round(_cache.put_latency_us, 0),
            "cold_get_total": round(_cache.cold_get_latency_us, 0),
            "cold_put_total": round(_cache.cold_put_latency_us, 0),
        },
    }


def cold_query_by_type(content_type: str, limit: int = 100) -> list[dict[str, Any]]:
    """Query cold storage entries by content type. Returns metadata list."""
    return _cache.cold_query_by_type(content_type, limit)


# ═══════════════════════════════════════════════════════════════════════════════
# Public Stats API
# ═══════════════════════════════════════════════════════════════════════════════


def get_stats() -> SessionStats:
    """Get the current session compression statistics."""
    # Sync hot tier stats
    _stats.cache_hits = _cache.hits
    _stats.cache_misses = _cache.misses
    _stats.cache_evictions = _cache.evictions
    _stats.cache_expirations = _cache.expirations
    _stats.cache_current_entries = _cache.hot_count
    _stats.cache_current_bytes = _cache.hot_bytes
    _stats.hot_hits = _cache.hot_hits
    # Sync latency
    _stats.get_latency_us = _cache.get_latency_us
    _stats.put_latency_us = _cache.put_latency_us
    _stats.cold_get_latency_us = _cache.cold_get_latency_us
    _stats.cold_put_latency_us = _cache.cold_put_latency_us
    # Sync cold tier stats
    _stats.cold_enabled = _cache.cold_enabled
    _stats.cold_entries = _cache.cold_count
    _stats.cold_bytes = _cache.cold_bytes
    _stats.cold_spills = _cache.cold_spills
    _stats.cold_promotions = _cache.cold_promotions
    _stats.cold_retrievals = _cache.cold_retrievals
    _stats.cold_hits = _cache.cold_hits
    _stats.cold_expirations = _cache._cold.expirations
    _stats.cold_rejects = _cache.cold_rejects
    _stats.cold_evicts = _cache.cold_evicts
    return _stats


def get_stats_summary() -> str:
    """Get a human-readable stats summary."""
    return get_stats().summary()


def get_stats_json() -> dict[str, Any]:
    """Get stats as a JSON-serializable dictionary."""
    return get_stats().to_dict()


def reset_stats() -> None:
    """Reset all session statistics."""
    global _stats
    _stats = SessionStats()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Content-aware context compressor (based on Headroom techniques)"
    )
    parser.add_argument(
        "--type",
        choices=[t.value for t in ContentType],
        help="Content type hint (auto-detect if omitted)",
    )
    parser.add_argument(
        "--file", "-f", help="Read content from file instead of stdin"
    )
    parser.add_argument(
        "--json-output", "-j", action="store_true", help="Output as JSON"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Show compression statistics after operation"
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear all cached entries"
    )
    args = parser.parse_args()

    if args.clear_cache:
        result = clear_cache()
        print(json.dumps(result, ensure_ascii=False))
        return

    # Read content
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    # Determine type
    content_type = ContentType(args.type) if args.type else None

    # Compress
    result = compress(content, content_type)

    if args.json_output:
        output = {
            "content": result.content,
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "tokens_saved": result.tokens_saved,
            "ratio": round(result.ratio, 3),
            "saved_pct": round(result.saved_pct, 1),
            "content_type": result.content_type.value,
            "cache_key": result.cache_key,
            "truncated_items": result.truncated_items,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(result.content)
        if result.cache_key:
            print(
                f"\n[Compressed: {result.original_tokens} -> {result.compressed_tokens} tokens "
                f"({result.saved_pct:.0f}% saved) | key: {result.cache_key}]"
            )

    if args.stats and not args.json_output:
        print()
        print(get_stats_summary())


if __name__ == "__main__":
    main()
