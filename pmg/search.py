from __future__ import annotations

import sqlite3

from .utils import normalize_entity_type


ENTITY_FIELDS = {
    "project": ("name", ["description", "goal", "current_stage", "hot_summary", "status"]),
    "question": ("title", ["original_text", "summary", "status", "question_type"]),
    "answer": ("summary", ["detail", "confidence", "status"]),
    "artifact": ("title", ["artifact_type", "summary", "file_path", "version", "status"]),
    "decision": ("title", ["decision", "reason", "alternatives", "impact", "status"]),
    "context": ("content", ["context_type", "importance", "status"]),
    "task": ("title", ["description", "status", "priority", "due_date"]),
    "session": ("title", ["summary", "raw_text"]),
    "source_material": ("title", ["source_type", "file_path", "summary", "processed_status"]),
}


def upsert_index(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    project_id: str | None,
    title: str | None,
    body: str | None,
    tags: str | None = None,
) -> None:
    entity_type = normalize_entity_type(entity_type)
    conn.execute(
        "DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    )
    conn.execute(
        """
        INSERT INTO search_index (entity_type, entity_id, project_id, title, body, tags)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, project_id, title or "", body or "", tags or ""),
    )


def index_row(conn: sqlite3.Connection, entity_type: str, row: sqlite3.Row | dict) -> None:
    entity_type = normalize_entity_type(entity_type)
    title_field, body_fields = ENTITY_FIELDS[entity_type]
    title = row[title_field] if title_field in row.keys() else ""
    body_parts = []
    for field in body_fields:
        if field in row.keys() and row[field]:
            body_parts.append(str(row[field]))
    project_id = row["id"] if entity_type == "project" else row["project_id"]
    upsert_index(conn, entity_type, row["id"], project_id, title, "\n".join(body_parts))


def search(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    params: list[object] = [query]
    project_filter = ""
    if project_id:
        project_filter = "AND project_id = ?"
        params.append(project_id)
    params.append(limit)
    try:
        rows = conn.execute(
            f"""
            SELECT entity_type, entity_id, project_id, title, body, tags, bm25(search_index) AS rank
            FROM search_index
            WHERE search_index MATCH ? {project_filter}
            ORDER BY rank
            LIMIT ?
            """,
            params,
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    if not rows:
        like = f"%{query}%"
        params = [like, like, like]
        project_filter = ""
        if project_id:
            project_filter = "AND project_id = ?"
            params.append(project_id)
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT entity_type, entity_id, project_id, title, body, tags, 0 AS rank
            FROM search_index
            WHERE (title LIKE ? OR body LIKE ? OR tags LIKE ?) {project_filter}
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]
