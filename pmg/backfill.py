from __future__ import annotations

from .capture import capture_candidates
from .repository import update_project_backfill_status


def start_backfill(conn, project: str) -> dict:
    return update_project_backfill_status(conn, project, "importing")


def complete_backfill(conn, project: str) -> dict:
    return update_project_backfill_status(conn, project, "completed")


def extract_from_sources(conn, project: str) -> dict:
    project_row = conn.execute("SELECT * FROM projects WHERE name = ? OR id = ?", (project, project)).fetchone()
    if not project_row:
        raise ValueError(f"Project not found: {project}")
    rows = conn.execute(
        """
        SELECT * FROM source_materials
        WHERE project_id = ? AND processed_status IN ('pending', 'failed')
        ORDER BY imported_at ASC
        """,
        (project_row["id"],),
    ).fetchall()
    merged = {"project": project_row["name"], "candidates": {"questions": [], "decisions": [], "artifacts": [], "contexts": [], "tasks": []}}
    for row in rows:
        text = row["raw_text"] or row["summary"] or row["title"]
        captured = capture_candidates(project_row["name"], text)
        for group, items in captured["candidates"].items():
            for item in items:
                item["source_material_id"] = row["id"]
                item["confidence"] = item.get("confidence", "medium")
                item["extraction_method"] = "keyword_rule"
                merged["candidates"][group].append(item)
        conn.execute("UPDATE source_materials SET processed_status = 'extracted', updated_at = datetime('now') WHERE id = ?", (row["id"],))
    update_project_backfill_status(conn, project_row["name"], "extracted")
    return merged


def review_backfill(conn, project: str) -> list[dict]:
    project_row = conn.execute("SELECT * FROM projects WHERE name = ? OR id = ?", (project, project)).fetchone()
    if not project_row:
        raise ValueError(f"Project not found: {project}")
    rows = conn.execute(
        "SELECT id, title, source_type, file_path, summary, processed_status FROM source_materials WHERE project_id = ? ORDER BY imported_at DESC",
        (project_row["id"],),
    ).fetchall()
    return [dict(row) for row in rows]
