from __future__ import annotations

import re
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

ENTITY_TABLES = {
    "project": "projects",
    "question": "questions",
    "answer": "answers",
    "artifact": "artifacts",
    "decision": "decisions",
    "context": "contexts",
    "task": "tasks",
    "session": "sessions",
    "source_material": "source_materials",
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


def query_terms(query: str) -> list[str]:
    return [term.lower() for term in re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", query) if term.strip()]


def fts_query(query: str) -> str:
    terms = query_terms(query)
    if not terms:
        return query
    return " OR ".join(f'"{term}"' for term in terms)


def row_text(row: sqlite3.Row, entity_type: str) -> tuple[str, str]:
    title_field, body_fields = ENTITY_FIELDS[entity_type]
    title = str(row[title_field] or "") if title_field in row.keys() else ""
    body = "\n".join(str(row[field]) for field in body_fields if field in row.keys() and row[field])
    return title, body


def table_search(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    terms = query_terms(query) or [query.lower()]
    rows: list[dict] = []
    for entity_type, table in ENTITY_TABLES.items():
        params: list[object] = []
        where = ""
        if project_id:
            if entity_type == "project":
                where = "WHERE id = ?"
            else:
                where = "WHERE project_id = ?"
            params.append(project_id)
        for row in conn.execute(f"SELECT * FROM {table} {where} ORDER BY updated_at DESC, created_at DESC LIMIT 200", params).fetchall():
            title, body = row_text(row, entity_type)
            haystack = "\n".join([entity_type, title, body]).lower()
            if any(term in haystack for term in terms):
                rows.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": row["id"],
                        "project_id": row["id"] if entity_type == "project" else row["project_id"],
                        "title": title,
                        "body": body,
                        "tags": "",
                        "rank": 1,
                    }
                )
                if len(rows) >= limit:
                    return rows
    return rows


def search(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()
    params: list[object] = [fts_query(query)]
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
    for row in rows:
        data = dict(row)
        key = (data["entity_type"], data["entity_id"])
        if key not in seen:
            results.append(data)
            seen.add(key)
    if len(results) < limit:
        terms = query_terms(query) or [query]
        clauses = []
        params = []
        for term in terms:
            like = f"%{term}%"
            clauses.append("(title LIKE ? OR body LIKE ? OR tags LIKE ? OR entity_type LIKE ?)")
            params.extend([like, like, like, like])
        project_filter = ""
        if project_id:
            project_filter = "AND project_id = ?"
            params.append(project_id)
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT entity_type, entity_id, project_id, title, body, tags, 0 AS rank
            FROM search_index
            WHERE ({" OR ".join(clauses)}) {project_filter}
            LIMIT ?
            """,
            params,
        ).fetchall()
        for row in rows:
            data = dict(row)
            key = (data["entity_type"], data["entity_id"])
            if key not in seen:
                results.append(data)
                seen.add(key)
                if len(results) >= limit:
                    break
    if len(results) < limit:
        for data in table_search(conn, query, project_id=project_id, limit=limit):
            key = (data["entity_type"], data["entity_id"])
            if key not in seen:
                results.append(data)
                seen.add(key)
                if len(results) >= limit:
                    break
    return results[:limit]
