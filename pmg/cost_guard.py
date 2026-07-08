from __future__ import annotations

import sqlite3

from .config import read_config, set_cost_mode
from .db import now_iso
from .utils import unique_id


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def status() -> dict:
    return read_config()["cost_guard"]


def update_mode(mode: str) -> dict:
    return set_cost_mode(mode)["cost_guard"]


def enforce_context_limit(text: str) -> tuple[str, bool]:
    limit = int(status().get("max_context_pack_chars", 6000))
    if len(text) <= limit:
        return text, False
    notice = "\n\nTrack Pack 已按默认预算截断。可使用 --more 或 --full 查看更多，但不会默认进入 AI 上下文。\n"
    return text[: max(0, limit - len(notice))].rstrip() + notice, True


def log_ai_call(
    conn: sqlite3.Connection,
    command: str,
    project_id: str | None,
    input_tokens: int,
    output_tokens: int,
    fulltext_included: bool,
    source_count: int,
) -> dict:
    row_id = unique_id(conn, "ai_call_logs", "ai", command)
    total = input_tokens + output_tokens
    conn.execute(
        """
        INSERT INTO ai_call_logs
        (id, command, project_id, input_token_estimate, output_token_estimate,
         total_token_estimate, fulltext_included, source_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (row_id, command, project_id, input_tokens, output_tokens, total, int(fulltext_included), source_count, now_iso()),
    )
    return dict(conn.execute("SELECT * FROM ai_call_logs WHERE id = ?", (row_id,)).fetchone())


def list_ai_logs(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM ai_call_logs ORDER BY created_at DESC LIMIT 50").fetchall()
    return [dict(row) for row in rows]
