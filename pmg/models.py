from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Project:
    id: str
    name: str
    description: str | None = None
    goal: str | None = None
    status: str = "active"
    current_stage: str | None = None
    hot_summary: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Question:
    id: str
    project_id: str
    title: str
    original_text: str | None = None
    summary: str | None = None
    status: str = "open"
    question_type: str = "unknown"
    importance_score: float = 0.5
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Answer:
    id: str
    project_id: str
    question_id: str | None
    summary: str
    detail: str | None = None
    confidence: str = "medium"
    status: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Artifact:
    id: str
    project_id: str
    title: str
    artifact_type: str = "other"
    summary: str | None = None
    content: str | None = None
    file_path: str | None = None
    version: str | None = None
    status: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Decision:
    id: str
    project_id: str
    title: str
    decision: str
    reason: str | None = None
    alternatives: str | None = None
    impact: str | None = None
    status: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Context:
    id: str
    project_id: str
    content: str
    context_type: str = "background"
    importance: str = "medium"
    status: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Session:
    id: str
    project_id: str
    title: str | None = None
    summary: str | None = None
    raw_text: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Relation:
    id: str
    source_type: str
    source_id: str
    relation_type: str
    target_type: str
    target_id: str
    weight: float = 1.0
    note: str | None = None
    created_at: str | None = None


def to_dict(instance) -> dict:
    return {k: v for k, v in asdict(instance).items() if v is not None}
