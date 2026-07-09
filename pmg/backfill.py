from __future__ import annotations

from pathlib import Path

from .capture import capture_candidates
from .importers import detect_source_type, first_heading_or_excerpt
from .repository import create_artifact, create_source_material, update_project_backfill_status


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".track",
    ".codex",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "coverage",
}

LIGHTWEIGHT_SUFFIXES = {".md", ".txt", ".json", ".py"}
PRIORITY_FILENAMES = {
    "readme.md",
    "agents.md",
    "changelog.md",
    "todo.md",
    "roadmap.md",
    "package.json",
    "pyproject.toml",
}
MAX_LIGHTWEIGHT_FILES = 24
MAX_LIGHTWEIGHT_FILE_CHARS = 24_000
MAX_LIGHTWEIGHT_TOTAL_CHARS = 160_000


def start_backfill(conn, project: str) -> dict:
    return update_project_backfill_status(conn, project, "importing")


def complete_backfill(conn, project: str) -> dict:
    return update_project_backfill_status(conn, project, "completed")


def lightweight_project_backfill(conn, project: str, root: str | Path = ".") -> dict:
    """Build a useful first local index without deep AI analysis."""
    root_path = Path(root).expanduser().resolve()
    start_backfill(conn, project)
    imported = []
    total_chars = 0

    for path in candidate_project_files(root_path):
        if total_chars >= MAX_LIGHTWEIGHT_TOTAL_CHARS:
            break
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        if not raw_text.strip():
            continue
        truncated = raw_text[:MAX_LIGHTWEIGHT_FILE_CHARS]
        total_chars += len(truncated)
        summary = lightweight_file_summary(truncated)
        source = create_source_material(
            conn,
            project,
            title=relative_title(root_path, path),
            source_type=detect_source_type(path),
            file_path=str(path),
            raw_text=truncated,
            summary=summary,
        )
        artifact = create_artifact(
            conn,
            project,
            title=relative_title(root_path, path),
            artifact_type=file_artifact_type(path),
            summary=summary,
            file_path=str(path),
            confidence="local_index",
            extraction_method="lightweight_backfill",
            source_material_id=source["id"],
        )
        imported.append(
            {
                "source_material_id": source["id"],
                "artifact_id": artifact["id"],
                "path": str(path),
                "chars": len(truncated),
            }
        )

    candidates = extract_from_sources(conn, project)
    project_row = complete_backfill(conn, project)
    return {
        "project": project,
        "root": str(root_path),
        "imported": imported,
        "candidates": candidates,
        "project_status": project_row,
    }


def candidate_project_files(root: Path) -> list[Path]:
    files = [path for path in root.rglob("*") if is_lightweight_file(root, path)]
    return sorted(files, key=lambda path: (priority_rank(root, path), len(path.parts), str(path)))[:MAX_LIGHTWEIGHT_FILES]


def is_lightweight_file(root: Path, path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() not in LIGHTWEIGHT_SUFFIXES:
        return False
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if any(part in SKIP_DIRS for part in rel.parts):
        return False
    return True


def priority_rank(root: Path, path: Path) -> int:
    rel = path.relative_to(root)
    name = path.name.lower()
    if name in PRIORITY_FILENAMES:
        return 0
    if rel.parts and rel.parts[0].lower() in {"docs", "doc", "specs", "spec", "notes"}:
        return 1
    if path.suffix.lower() in {".md", ".txt"}:
        return 2
    if path.suffix.lower() == ".json":
        return 3
    return 4


def relative_title(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def lightweight_file_summary(text: str, limit: int = 320) -> str:
    heading = first_heading_or_excerpt(text, 100)
    compact = " ".join(text.split())
    if compact.startswith(heading):
        return compact[:limit]
    return f"{heading} {compact}"[:limit]


def file_artifact_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "code"
    if suffix == ".md":
        return "document"
    if suffix == ".json":
        return "config"
    return "memo"


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
