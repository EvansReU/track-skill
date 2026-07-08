from __future__ import annotations

import sqlite3

from .db import now_iso
from .search import index_row
from .utils import normalize_entity_type, table_for, unique_id


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def create_project(
    conn: sqlite3.Connection,
    name: str,
    description: str | None = None,
    goal: str | None = None,
    status: str = "active",
    stage: str | None = None,
    hot_summary: str | None = None,
    origin_type: str = "new_tracked",
    backfill_status: str = "not_started",
) -> dict:
    ts = now_iso()
    project_id = unique_id(conn, "projects", "project", name)
    conn.execute(
        """
        INSERT INTO projects
        (id, name, description, goal, status, current_stage, hot_summary, origin_type, backfill_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, name, description, goal, status, stage, hot_summary, origin_type, backfill_status, ts, ts),
    )
    row = get_by_id(conn, "project", project_id)
    index_row(conn, "project", row)
    return dict(row)


def enter_project(conn: sqlite3.Connection, name: str) -> tuple[dict, bool]:
    project = get_project(conn, name)
    if project:
        return project, False
    created = create_project(conn, name, hot_summary="New local Track project.")
    return created, True


def get_project(conn: sqlite3.Connection, name_or_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM projects WHERE name = ? OR id = ?",
        (name_or_id, name_or_id),
    ).fetchone()
    return row_to_dict(row)


def require_project(conn: sqlite3.Connection, name_or_id: str) -> dict:
    project = get_project(conn, name_or_id)
    if not project:
        raise ValueError(f"Project not found: {name_or_id}")
    return project


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC, name").fetchall()
    return [dict(row) for row in rows]


def update_project_summary(conn: sqlite3.Connection, name_or_id: str, summary: str) -> dict:
    project = require_project(conn, name_or_id)
    conn.execute(
        "UPDATE projects SET hot_summary = ?, updated_at = ? WHERE id = ?",
        (summary, now_iso(), project["id"]),
    )
    row = get_by_id(conn, "project", project["id"])
    index_row(conn, "project", row)
    return dict(row)


def create_question(
    conn: sqlite3.Connection,
    project: str,
    title: str,
    text: str | None = None,
    summary: str | None = None,
    status: str = "open",
    question_type: str = "unknown",
    importance_score: float = 0.5,
    confidence: str = "user_confirmed",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "questions", "q", title)
    conn.execute(
        """
        INSERT INTO questions
        (id, project_id, title, original_text, summary, status, question_type, importance_score,
         confidence, extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            project_row["id"],
            title,
            text,
            summary,
            status,
            question_type,
            importance_score,
            confidence,
            extraction_method,
            source_material_id,
            ts,
            ts,
        ),
    )
    row = get_by_id(conn, "question", item_id)
    index_row(conn, "question", row)
    create_relation(conn, "question", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_answer(
    conn: sqlite3.Connection,
    project: str,
    summary: str,
    question_id: str | None = None,
    detail: str | None = None,
    confidence: str = "medium",
    status: str = "active",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "answers", "a", summary[:40])
    conn.execute(
        """
        INSERT INTO answers
        (id, project_id, question_id, summary, detail, confidence, status,
         extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, project_row["id"], question_id, summary, detail, confidence, status, extraction_method, source_material_id, ts, ts),
    )
    row = get_by_id(conn, "answer", item_id)
    index_row(conn, "answer", row)
    create_relation(conn, "answer", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    if question_id:
        create_relation(conn, "answer", item_id, "answers", "question", question_id)
    return dict(row)


def create_artifact(
    conn: sqlite3.Connection,
    project: str,
    title: str,
    artifact_type: str = "other",
    summary: str | None = None,
    content: str | None = None,
    file_path: str | None = None,
    version: str | None = None,
    status: str = "active",
    confidence: str = "user_confirmed",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "artifacts", "artifact", title)
    conn.execute(
        """
        INSERT INTO artifacts
        (id, project_id, title, artifact_type, summary, content, file_path, version, status,
         confidence, extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            project_row["id"],
            title,
            artifact_type,
            summary,
            content,
            file_path,
            version,
            status,
            confidence,
            extraction_method,
            source_material_id,
            ts,
            ts,
        ),
    )
    row = get_by_id(conn, "artifact", item_id)
    index_row(conn, "artifact", row)
    create_relation(conn, "artifact", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_decision(
    conn: sqlite3.Connection,
    project: str,
    title: str,
    decision: str,
    reason: str | None = None,
    alternatives: str | None = None,
    impact: str | None = None,
    status: str = "active",
    confidence: str = "user_confirmed",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "decisions", "decision", title)
    conn.execute(
        """
        INSERT INTO decisions
        (id, project_id, title, decision, reason, alternatives, impact, status,
         confidence, extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            project_row["id"],
            title,
            decision,
            reason,
            alternatives,
            impact,
            status,
            confidence,
            extraction_method,
            source_material_id,
            ts,
            ts,
        ),
    )
    row = get_by_id(conn, "decision", item_id)
    index_row(conn, "decision", row)
    create_relation(conn, "decision", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_context(
    conn: sqlite3.Connection,
    project: str,
    content: str,
    context_type: str = "background",
    importance: str = "medium",
    status: str = "active",
    confidence: str = "user_confirmed",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "contexts", "context", content[:40])
    conn.execute(
        """
        INSERT INTO contexts
        (id, project_id, content, context_type, importance, status,
         confidence, extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, project_row["id"], content, context_type, importance, status, confidence, extraction_method, source_material_id, ts, ts),
    )
    row = get_by_id(conn, "context", item_id)
    index_row(conn, "context", row)
    create_relation(conn, "context", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_task(
    conn: sqlite3.Connection,
    project: str,
    title: str,
    description: str | None = None,
    status: str = "todo",
    priority: str = "medium",
    due_date: str | None = None,
    confidence: str = "user_confirmed",
    extraction_method: str = "manual",
    source_material_id: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "tasks", "task", title)
    conn.execute(
        """
        INSERT INTO tasks
        (id, project_id, title, description, status, priority, due_date,
         confidence, extraction_method, source_material_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, project_row["id"], title, description, status, priority, due_date, confidence, extraction_method, source_material_id, ts, ts),
    )
    row = get_by_id(conn, "task", item_id)
    index_row(conn, "task", row)
    create_relation(conn, "task", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_session(
    conn: sqlite3.Connection,
    project: str,
    title: str | None = None,
    summary: str | None = None,
    raw_text: str | None = None,
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "sessions", "session", title or summary or "session")
    conn.execute(
        """
        INSERT INTO sessions
        (id, project_id, title, summary, raw_text, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, project_row["id"], title, summary, raw_text, ts, ts),
    )
    row = get_by_id(conn, "session", item_id)
    index_row(conn, "session", row)
    create_relation(conn, "session", item_id, "belongs_to", "project", project_row["id"], note="Auto-created project membership.")
    return dict(row)


def create_source_material(
    conn: sqlite3.Connection,
    project: str,
    title: str,
    source_type: str = "unknown",
    file_path: str | None = None,
    raw_text: str | None = None,
    summary: str | None = None,
    processed_status: str = "pending",
) -> dict:
    project_row = require_project(conn, project)
    ts = now_iso()
    item_id = unique_id(conn, "source_materials", "source", title)
    conn.execute(
        """
        INSERT INTO source_materials
        (id, project_id, title, source_type, file_path, raw_text, summary, imported_at, processed_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, project_row["id"], title, source_type, file_path, raw_text, summary, ts, processed_status, ts, ts),
    )
    row = get_by_id(conn, "source_material", item_id)
    index_row(conn, "source_material", row)
    create_relation(conn, "source_material", item_id, "belongs_to", "project", project_row["id"], note="Imported source material.")
    return dict(row)


def update_project_backfill_status(conn: sqlite3.Connection, project: str, status: str) -> dict:
    project_row = require_project(conn, project)
    backfilled_at = now_iso() if status == "completed" else project_row.get("backfilled_at")
    origin_type = "backfilled" if status == "completed" and project_row.get("origin_type") == "new_tracked" else project_row.get("origin_type")
    conn.execute(
        """
        UPDATE projects
        SET backfill_status = ?, backfilled_at = ?, origin_type = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, backfilled_at, origin_type, now_iso(), project_row["id"]),
    )
    row = get_by_id(conn, "project", project_row["id"])
    index_row(conn, "project", row)
    return dict(row)


def create_relation(
    conn: sqlite3.Connection,
    source_type: str,
    source_id: str,
    relation_type: str,
    target_type: str,
    target_id: str,
    weight: float = 1.0,
    note: str | None = None,
) -> dict:
    source_type = normalize_entity_type(source_type)
    target_type = normalize_entity_type(target_type)
    ts = now_iso()
    rel_id = unique_id(conn, "relations", "rel", f"{source_type}-{source_id}-{relation_type}-{target_type}-{target_id}")
    conn.execute(
        """
        INSERT INTO relations
        (id, source_type, source_id, relation_type, target_type, target_id, weight, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (rel_id, source_type, source_id, relation_type, target_type, target_id, weight, note, ts),
    )
    return dict(conn.execute("SELECT * FROM relations WHERE id = ?", (rel_id,)).fetchone())


def get_by_id(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> sqlite3.Row | None:
    table = table_for(entity_type)
    return conn.execute(f"SELECT * FROM {table} WHERE id = ?", (entity_id,)).fetchone()


def list_project_items(conn: sqlite3.Connection, project_id: str, table: str, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE project_id = ? ORDER BY updated_at DESC, created_at DESC LIMIT ?",
        (project_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]
