from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DATA_DIR = Path(os.environ.get("TRACK_HOME", "~/.track")).expanduser()
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "track.sqlite"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    goal TEXT,
    status TEXT,
    current_stage TEXT,
    hot_summary TEXT,
    origin_type TEXT DEFAULT 'new_tracked',
    backfill_status TEXT DEFAULT 'not_started',
    backfilled_at TEXT,
    source_summary TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    original_text TEXT,
    summary TEXT,
    status TEXT,
    question_type TEXT,
    importance_score REAL,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    question_id TEXT,
    summary TEXT NOT NULL,
    detail TEXT,
    confidence TEXT,
    status TEXT,
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    artifact_type TEXT,
    summary TEXT,
    content TEXT,
    file_path TEXT,
    version TEXT,
    status TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    alternatives TEXT,
    impact TEXT,
    status TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS contexts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    content TEXT NOT NULL,
    context_type TEXT,
    importance TEXT,
    status TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT,
    priority TEXT,
    due_date TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT,
    summary TEXT,
    raw_text TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS source_materials (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    source_type TEXT,
    file_path TEXT,
    raw_text TEXT,
    summary TEXT,
    imported_at TEXT,
    processed_status TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    note TEXT,
    confidence TEXT DEFAULT 'user_confirmed',
    extraction_method TEXT DEFAULT 'manual',
    source_material_id TEXT,
    created_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    entity_type,
    entity_id UNINDEXED,
    project_id UNINDEXED,
    title,
    body,
    tags
);

CREATE TABLE IF NOT EXISTS ai_call_logs (
    id TEXT PRIMARY KEY,
    command TEXT,
    project_id TEXT,
    input_token_estimate INTEGER,
    output_token_estimate INTEGER,
    total_token_estimate INTEGER,
    fulltext_included INTEGER,
    source_count INTEGER,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_questions_project ON questions(project_id);
CREATE INDEX IF NOT EXISTS idx_answers_project ON answers(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_contexts_project ON contexts(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_source_materials_project ON source_materials(project_id);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target_type, target_id);
"""

MIGRATIONS = {
    "projects": {
        "origin_type": "TEXT DEFAULT 'new_tracked'",
        "backfill_status": "TEXT DEFAULT 'not_started'",
        "backfilled_at": "TEXT",
        "source_summary": "TEXT",
    },
    "questions": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "answers": {"extraction_method": "TEXT DEFAULT 'manual'", "source_material_id": "TEXT"},
    "artifacts": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "decisions": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "contexts": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "tasks": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "sessions": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
    "relations": {
        "confidence": "TEXT DEFAULT 'user_confirmed'",
        "extraction_method": "TEXT DEFAULT 'manual'",
        "source_material_id": "TEXT",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path).expanduser() if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path | None = None) -> Path:
    path = Path(db_path).expanduser() if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        apply_migrations(conn)
    return path


def apply_migrations(conn: sqlite3.Connection) -> None:
    for table, columns in MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, spec in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")
