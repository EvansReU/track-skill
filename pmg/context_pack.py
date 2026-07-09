from __future__ import annotations

import sqlite3

from .db import now_iso
from .relations import get_relations_for, related_items
from .render import json_output, render_items, simple_yaml
from .repository import get_by_id, list_project_items, require_project
from .search import search


LIMITS = {
    "questions": 5,
    "answers": 5,
    "decisions": 5,
    "artifacts": 5,
    "contexts": 5,
    "tasks": 5,
}


TYPE_TO_GROUP = {
    "question": "questions",
    "answer": "answers",
    "decision": "decisions",
    "artifact": "artifacts",
    "context": "contexts",
    "task": "tasks",
}


def empty_groups() -> dict[str, list[dict]]:
    return {name: [] for name in LIMITS}


def add_item(groups: dict[str, list[dict]], entity_type: str, item: dict) -> None:
    group = TYPE_TO_GROUP.get(entity_type)
    if not group:
        return
    if len(groups[group]) >= LIMITS[group]:
        return
    if any(existing["id"] == item["id"] for existing in groups[group]):
        return
    groups[group].append(item)


def build_project_context_pack(conn: sqlite3.Connection, project_name: str) -> dict:
    project = require_project(conn, project_name)
    groups = empty_groups()
    for table, group in (
        ("questions", "questions"),
        ("answers", "answers"),
        ("decisions", "decisions"),
        ("artifacts", "artifacts"),
        ("contexts", "contexts"),
        ("tasks", "tasks"),
    ):
        rows = list_project_items(conn, project["id"], table, LIMITS[group] * 2)
        for row in rows:
            if group == "questions" and row.get("status") not in ("open", "answered", "blocked"):
                continue
            if group == "decisions" and row.get("status") != "active":
                continue
            if group == "artifacts" and row.get("status") not in ("active", "draft"):
                continue
            if group == "tasks" and row.get("status") not in ("todo", "doing", "blocked"):
                continue
            if len(groups[group]) < LIMITS[group]:
                groups[group].append(row)
    return {
        "context_pack": {
            "query": None,
            "generated_at": now_iso(),
            "project": project_fields(project),
            "matched_items": compact_groups(groups),
            "related_graph": [],
            "suggested_next_steps": suggest_next_steps(groups),
        }
    }


def build_recall_context_pack(
    conn: sqlite3.Connection,
    query: str,
    project_name: str | None = None,
    top_k: int = 10,
    depth: int = 1,
) -> dict:
    project = require_project(conn, project_name) if project_name else None
    project_id = project["id"] if project else None
    hits = search(conn, query, project_id=project_id, limit=top_k)
    groups = empty_groups()
    graph: list[dict] = []
    seen_graph: set[str] = set()

    for hit in hits:
        entity_type = hit["entity_type"]
        entity_id = hit["entity_id"]
        item = get_by_id(conn, entity_type, entity_id)
        if item:
            add_item(groups, entity_type, dict(item))
        rels = get_relations_for(conn, entity_type, entity_id, depth=depth)
        for rel in rels:
            if rel["id"] not in seen_graph:
                graph.append(
                    {
                        "source": f"{rel['source_type']}:{rel['source_id']}",
                        "relation": rel["relation_type"],
                        "target": f"{rel['target_type']}:{rel['target_id']}",
                        "note": rel["note"],
                        "confidence": rel.get("confidence"),
                    }
                )
                seen_graph.add(rel["id"])
        for related in related_items(conn, rels):
            add_item(groups, related.pop("_entity_type"), related)

    if not project and hits:
        first_project_id = hits[0].get("project_id")
        row = get_by_id(conn, "project", first_project_id) if first_project_id else None
        project = dict(row) if row else None

    return {
        "context_pack": {
            "query": query,
            "generated_at": now_iso(),
            "project": project_fields(project) if project else None,
            "matched_items": compact_groups(groups),
            "related_graph": graph[:15],
            "suggested_next_steps": suggest_next_steps(groups, query),
        }
    }


def project_fields(project: dict) -> dict:
    return {
        "id": project["id"],
        "name": project["name"],
        "goal": project.get("goal"),
        "current_stage": project.get("current_stage"),
        "hot_summary": project.get("hot_summary"),
        "origin_type": project.get("origin_type"),
        "backfill_status": project.get("backfill_status"),
        "tracked": project.get("tracked"),
        "auto_track_enabled": project.get("auto_track_enabled"),
        "last_auto_tracked_at": project.get("last_auto_tracked_at"),
    }


def compact_groups(groups: dict[str, list[dict]]) -> dict:
    return {
        "questions": [
            {"id": x["id"], "title": x["title"], "status": x["status"], "summary": x["summary"], "confidence": x.get("confidence")}
            for x in groups["questions"]
        ],
        "answers": [
            {"id": x["id"], "summary": x["summary"], "confidence": x["confidence"], "status": x["status"]}
            for x in groups["answers"]
        ],
        "decisions": [
            {
                "id": x["id"],
                "title": x["title"],
                "decision": x["decision"],
                "reason": x["reason"],
                "status": x["status"],
                "confidence": x.get("confidence"),
            }
            for x in groups["decisions"]
        ],
        "artifacts": [
            {
                "id": x["id"],
                "title": x["title"],
                "artifact_type": x["artifact_type"],
                "summary": x["summary"],
                "status": x["status"],
                "file_path": x["file_path"],
                "confidence": x.get("confidence"),
            }
            for x in groups["artifacts"]
        ],
        "contexts": [
            {
                "id": x["id"],
                "content": x["content"],
                "context_type": x["context_type"],
                "importance": x["importance"],
                "confidence": x.get("confidence"),
            }
            for x in groups["contexts"]
        ],
        "tasks": [
            {"id": x["id"], "title": x["title"], "status": x["status"], "priority": x["priority"], "confidence": x.get("confidence")}
            for x in groups["tasks"]
        ],
    }


def suggest_next_steps(groups: dict[str, list[dict]], query: str | None = None) -> list[str]:
    steps = []
    if groups["tasks"]:
        steps.append("Continue with the highest-priority open task.")
    if groups["questions"]:
        steps.append("Resolve or validate the most relevant open question.")
    if groups["decisions"]:
        steps.append("Use the active decisions as constraints before changing direction.")
    if not steps:
        topic = f" for '{query}'" if query else ""
        steps.append(f"Add more project memory nodes{topic} before relying on this context pack.")
    return steps[:3]


def render_context_pack(pack: dict, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json_output(pack)
    if output_format == "yaml":
        return simple_yaml(pack)
    cp = pack["context_pack"]
    project = cp.get("project") or {}
    lines = ["# Track Pack", ""]
    if cp.get("query"):
        lines += ["## Query", "", str(cp["query"]), ""]
    lines += [
        "## Project",
        "",
        project.get("name") or "_None._",
        "",
        "## Project Summary",
        "",
        project.get("hot_summary") or project.get("goal") or "_None._",
        "",
    ]
    items = cp["matched_items"]
    lines += render_items("Related Questions", items["questions"], lambda x: f"{x['title']} [{x['status']}/{x.get('confidence') or 'unknown'}]")
    lines += render_items("Related Answers", items["answers"], lambda x: f"{x['summary']} [{x['confidence']}/{x['status']}]")
    lines += render_items("Related Decisions", items["decisions"], lambda x: f"{x['title']}: {x['decision']} [{x.get('confidence') or 'unknown'}]")
    lines += render_items("Related Artifacts", items["artifacts"], lambda x: f"{x['title']} ({x['artifact_type']}) - {x.get('summary') or ''} [{x.get('confidence') or 'unknown'}]")
    lines += render_items("Related Contexts", items["contexts"], lambda x: f"{x['content']} ({x['context_type']}/{x['importance']}/{x.get('confidence') or 'unknown'})")
    lines += render_items("Related Tasks", items["tasks"], lambda x: f"{x['title']} [{x['status']}/{x['priority']}/{x.get('confidence') or 'unknown'}]")
    lines += ["## Related Graph", ""]
    if cp["related_graph"]:
        for rel in cp["related_graph"]:
            note = f" - {rel['note']}" if rel.get("note") else ""
            lines.append(f"- {rel['source']} --{rel['relation']}--> {rel['target']}{note}")
    else:
        lines.append("_None._")
    lines += ["", "## Suggested Next Steps", ""]
    for step in cp["suggested_next_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines).strip() + "\n"


def build_recall_brief(
    conn: sqlite3.Connection,
    query: str,
    project_name: str | None = None,
    top_k: int = 10,
    depth: int = 1,
) -> dict:
    pack = build_recall_context_pack(conn, query, project_name, top_k, depth)
    cp = pack["context_pack"]
    items = cp["matched_items"]
    return {
        "recall_brief": {
            "query": query,
            "generated_at": cp["generated_at"],
            "project": cp["project"],
            "answer": infer_brief_answer(query, items),
            "background": brief_background(items),
            "key_decisions": items["decisions"],
            "related_questions": items["questions"],
            "related_contexts": items["contexts"],
            "related_artifacts": items["artifacts"],
            "open_tasks": items["tasks"],
            "source_trail": cp["related_graph"],
            "current_status": infer_current_status(items),
            "next_prompts": suggest_memory_prompts(query, items),
        }
    }


def infer_brief_answer(query: str, items: dict) -> str:
    if items["decisions"]:
        decision = items["decisions"][0]
        return f"与「{query}」最相关的当前决策是：{decision['decision']}"
    if items["questions"]:
        question = items["questions"][0]
        return f"与「{query}」最相关的历史问题是：{question['title']}"
    if items["contexts"]:
        context = items["contexts"][0]
        return f"与「{query}」最相关的上下文是：{context['content']}"
    if items["artifacts"]:
        artifact = items["artifacts"][0]
        return f"与「{query}」最相关的产出物是：{artifact['title']}"
    return f"暂时没有找到足够明确的历史记录来还原「{query}」。"


def brief_background(items: dict) -> list[str]:
    background: list[str] = []
    for question in items["questions"][:2]:
        background.append(f"当时的问题：{question['title']}")
    for context in items["contexts"][:2]:
        background.append(f"当时的约束/背景：{context['content']}")
    return background


def infer_current_status(items: dict) -> list[str]:
    status: list[str] = []
    for decision in items["decisions"][:3]:
        status.append(f"仍需按决策状态判断：{decision['title']} [{decision.get('status') or 'unknown'}/{decision.get('confidence') or 'unknown'}]")
    for task in items["tasks"][:3]:
        status.append(f"相关任务：{task['title']} [{task.get('status') or 'unknown'}]")
    if not status:
        status.append("没有找到明确的当前状态记录。")
    return status


def suggest_memory_prompts(query: str, items: dict) -> list[str]:
    prompts = [f"继续追溯「{query}」的来源关系"]
    if items["decisions"]:
        prompts.append("查看这些决策是否仍然有效")
    if items["artifacts"]:
        prompts.append("追溯相关产出物是由哪个问题或决策触发的")
    if items["tasks"]:
        prompts.append("查看相关待办是否已经完成或被废弃")
    return prompts[:4]


def render_recall_brief(brief: dict, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json_output(brief)
    if output_format == "yaml":
        return simple_yaml(brief)
    rb = brief["recall_brief"]
    project = rb.get("project") or {}
    lines = [
        "# Track 回忆包",
        "",
        "## 你问的是",
        "",
        str(rb["query"]),
        "",
        "## 一句话帮你想起来",
        "",
        rb["answer"],
        "",
        "## 当时的背景",
        "",
    ]
    lines += [f"- {item}" for item in rb["background"]] or ["_没有找到明确背景。_"]
    lines += ["", "## 关键决策", ""]
    lines += [f"- {x['title']}：{x['decision']} [{x.get('status') or 'unknown'}/{x.get('confidence') or 'unknown'}]" for x in rb["key_decisions"]] or ["_没有找到相关决策。_"]
    lines += ["", "## 相关问题", ""]
    lines += [f"- {x['title']} [{x.get('status') or 'unknown'}/{x.get('confidence') or 'unknown'}]" for x in rb["related_questions"]] or ["_没有找到相关问题。_"]
    lines += ["", "## 相关上下文", ""]
    lines += [f"- {x['content']} [{x.get('context_type') or 'unknown'}/{x.get('importance') or 'unknown'}/{x.get('confidence') or 'unknown'}]" for x in rb["related_contexts"]] or ["_没有找到相关上下文。_"]
    lines += ["", "## 相关产出物", ""]
    lines += [f"- {x['title']} ({x.get('artifact_type') or 'other'})：{x.get('summary') or ''} [{x.get('confidence') or 'unknown'}]" for x in rb["related_artifacts"]] or ["_没有找到相关产出物。_"]
    lines += ["", "## 当前状态", ""]
    lines += [f"- {item}" for item in rb["current_status"]]
    lines += ["", "## 可追溯线索", ""]
    if rb["source_trail"]:
        for rel in rb["source_trail"][:8]:
            note = f" - {rel['note']}" if rel.get("note") else ""
            lines.append(f"- {rel['source']} --{rel['relation']}--> {rel['target']}{note}")
    else:
        lines.append("_没有找到明确关系链。_")
    lines += ["", "## 你可以继续问", ""]
    lines += [f"- {prompt}" for prompt in rb["next_prompts"]]
    if project.get("name"):
        lines += ["", f"_Project: {project['name']}_"]
    return "\n".join(lines).strip() + "\n"
