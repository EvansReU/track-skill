from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from uuid import uuid4


PREFIXES = {
    "projects": "project",
    "questions": "q",
    "answers": "a",
    "artifacts": "artifact",
    "decisions": "decision",
    "contexts": "context",
    "tasks": "task",
    "sessions": "session",
    "source_materials": "source",
    "relations": "rel",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9_\-\u4e00-\u9fff]+", "", value)
    return value.strip("-") or uuid4().hex[:8]


def make_id(prefix: str, value: str | None = None) -> str:
    if value:
        return f"{prefix}_{slugify(value)}"[:96]
    return f"{prefix}_{uuid4().hex[:10]}"


def unique_id(conn: sqlite3.Connection, table: str, prefix: str, seed: str | None = None) -> str:
    base = make_id(prefix, seed)
    candidate = base
    n = 2
    while conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (candidate,)).fetchone():
        candidate = f"{base}_{n}"
        n += 1
    return candidate


def parse_ref(ref: str) -> tuple[str, str]:
    if ":" not in ref:
        raise ValueError("Reference must use type:id, for example question:q_001")
    entity_type, entity_id = ref.split(":", 1)
    entity_type = normalize_entity_type(entity_type)
    if not entity_id:
        raise ValueError("Reference id cannot be empty")
    return entity_type, entity_id


def normalize_entity_type(value: str) -> str:
    value = value.strip().lower()
    singular = {
        "project": "project",
        "projects": "project",
        "question": "question",
        "questions": "question",
        "answer": "answer",
        "answers": "answer",
        "artifact": "artifact",
        "artifacts": "artifact",
        "decision": "decision",
        "decisions": "decision",
        "context": "context",
        "contexts": "context",
        "task": "task",
        "tasks": "task",
        "session": "session",
        "sessions": "session",
        "source": "source_material",
        "source_material": "source_material",
        "source_materials": "source_material",
    }
    if value not in singular:
        raise ValueError(f"Unsupported entity type: {value}")
    return singular[value]


def table_for(entity_type: str) -> str:
    return {
        "project": "projects",
        "question": "questions",
        "answer": "answers",
        "artifact": "artifacts",
        "decision": "decisions",
        "context": "contexts",
        "task": "tasks",
        "session": "sessions",
        "source_material": "source_materials",
    }[normalize_entity_type(entity_type)]


def read_json(path: str | Path) -> dict:
    with Path(path).expanduser().open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
