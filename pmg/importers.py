from __future__ import annotations

from pathlib import Path

from .repository import create_source_material


SUPPORTED_SUFFIXES = {".md", ".txt", ".json", ".py"}


def detect_source_type(path: Path | None, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if not path:
        return "chat_log"
    suffix = path.suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix == ".py":
        return "code"
    if suffix == ".json":
        return "document"
    if suffix == ".txt":
        return "memo"
    return "unknown"


def import_file(conn, project: str, path: str, source_type: str | None = None) -> dict:
    file_path = Path(path).expanduser()
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(f"File not found: {path}")
    if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    raw_text = file_path.read_text(encoding="utf-8", errors="replace")
    summary = first_heading_or_excerpt(raw_text)
    return create_source_material(
        conn,
        project,
        title=file_path.name,
        source_type=detect_source_type(file_path, source_type),
        file_path=str(file_path),
        raw_text=raw_text,
        summary=summary,
    )


def import_folder(conn, project: str, path: str, recursive: bool = False) -> list[dict]:
    folder = Path(path).expanduser()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Folder not found: {path}")
    pattern = "**/*" if recursive else "*"
    imported = []
    for item in sorted(folder.glob(pattern)):
        if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES:
            imported.append(import_file(conn, project, str(item)))
    return imported


def import_text(conn, project: str, title: str, text: str, source_type: str = "chat_log") -> dict:
    return create_source_material(
        conn,
        project,
        title=title,
        source_type=source_type,
        raw_text=text,
        summary=first_heading_or_excerpt(text),
    )


def first_heading_or_excerpt(text: str, limit: int = 240) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:limit]
    compact = " ".join(text.split())
    return compact[:limit]
