from __future__ import annotations

import sqlite3

from .repository import create_relation, get_by_id
from .utils import normalize_entity_type


VALID_RELATION_TYPES = {
    "belongs_to",
    "triggered_by",
    "answers",
    "answered_by",
    "derived_from",
    "supersedes",
    "superseded_by",
    "contradicts",
    "depends_on",
    "blocks",
    "related_to",
    "cites",
    "led_to",
    "affects",
    "produced",
    "has_context",
    "has_task",
    "mentions",
}


def add_relation(
    conn: sqlite3.Connection,
    source_type: str,
    source_id: str,
    relation_type: str,
    target_type: str,
    target_id: str,
    weight: float = 1.0,
    note: str | None = None,
) -> dict:
    if relation_type not in VALID_RELATION_TYPES:
        raise ValueError(f"Unsupported relation_type: {relation_type}")
    return create_relation(conn, source_type, source_id, relation_type, target_type, target_id, weight, note)


def get_relations_for(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    depth: int = 1,
) -> list[dict]:
    entity_type = normalize_entity_type(entity_type)
    seen_nodes = {(entity_type, entity_id)}
    frontier = [(entity_type, entity_id)]
    relations: list[dict] = []
    seen_relations: set[str] = set()

    for _ in range(depth):
        next_frontier: list[tuple[str, str]] = []
        for current_type, current_id in frontier:
            rows = conn.execute(
                """
                SELECT * FROM relations
                WHERE (source_type = ? AND source_id = ?)
                   OR (target_type = ? AND target_id = ?)
                ORDER BY weight DESC, created_at DESC
                """,
                (current_type, current_id, current_type, current_id),
            ).fetchall()
            for row in rows:
                rel = dict(row)
                if rel["id"] not in seen_relations:
                    relations.append(rel)
                    seen_relations.add(rel["id"])
                for node in ((rel["source_type"], rel["source_id"]), (rel["target_type"], rel["target_id"])):
                    if node not in seen_nodes:
                        seen_nodes.add(node)
                        next_frontier.append(node)
        frontier = next_frontier
        if not frontier:
            break
    return relations


def related_items(conn: sqlite3.Connection, relations: list[dict]) -> list[dict]:
    items: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for rel in relations:
        for entity_type, entity_id in (
            (rel["source_type"], rel["source_id"]),
            (rel["target_type"], rel["target_id"]),
        ):
            key = (entity_type, entity_id)
            if key in seen:
                continue
            seen.add(key)
            row = get_by_id(conn, entity_type, entity_id)
            if row:
                item = dict(row)
                item["_entity_type"] = entity_type
                items.append(item)
    return items


def format_node(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"
