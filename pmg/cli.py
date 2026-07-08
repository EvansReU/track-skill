from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backfill import complete_backfill, extract_from_sources, review_backfill, start_backfill
from .capture import capture_candidates
from .config import LATEST_CANDIDATES_PATH, get_current_project, init_config, set_current_project
from .context_pack import build_project_context_pack, build_recall_context_pack, render_context_pack
from .cost_guard import enforce_context_limit, estimate_tokens, list_ai_logs, status as cost_status, update_mode
from .db import DEFAULT_DB_PATH, connect, init_db
from .importers import import_file, import_folder, import_text
from .relations import add_relation, get_relations_for
from .render import json_output, simple_yaml
from .repository import (
    create_answer,
    create_artifact,
    create_context,
    create_decision,
    create_project,
    create_question,
    create_session,
    create_task,
    enter_project,
    get_project,
    list_projects,
    update_project_summary,
)
from .search import search
from .utils import parse_ref, read_json


KNOWN_COMMANDS = {
    "init",
    "project",
    "question",
    "answer",
    "artifact",
    "decision",
    "context",
    "task",
    "session",
    "relation",
    "search",
    "recall",
    "context-pack",
    "capture",
    "save-candidates",
    "this",
    "save",
    "查",
    "pack",
    "file",
    "import",
    "backfill",
    "cost",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="track", description="Track local project memory CLI")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize local Track database and config")

    project = sub.add_parser("project", help="Manage projects")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_enter = project_sub.add_parser("enter")
    project_enter.add_argument("name")
    project_create = project_sub.add_parser("create")
    project_create.add_argument("--name", required=True)
    project_create.add_argument("--description")
    project_create.add_argument("--goal")
    project_create.add_argument("--status", default="active")
    project_create.add_argument("--stage")
    project_create.add_argument("--summary")
    project_show = project_sub.add_parser("show")
    project_show.add_argument("project")
    project_sub.add_parser("list")
    project_summary = project_sub.add_parser("update-summary")
    project_summary.add_argument("project")
    project_summary.add_argument("--summary", required=True)

    question = sub.add_parser("question")
    question_sub = question.add_subparsers(dest="question_command", required=True)
    question_add = question_sub.add_parser("add")
    question_add.add_argument("--project")
    question_add.add_argument("--title", required=True)
    question_add.add_argument("--text")
    question_add.add_argument("--summary")
    question_add.add_argument("--status", default="open")
    question_add.add_argument("--type", default="unknown", dest="question_type")
    question_add.add_argument("--importance", type=float, default=0.5)

    answer = sub.add_parser("answer")
    answer_sub = answer.add_subparsers(dest="answer_command", required=True)
    answer_add = answer_sub.add_parser("add")
    answer_add.add_argument("--project")
    answer_add.add_argument("--question")
    answer_add.add_argument("--summary", required=True)
    answer_add.add_argument("--detail")
    answer_add.add_argument("--confidence", default="medium")
    answer_add.add_argument("--status", default="active")

    artifact = sub.add_parser("artifact")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_add = artifact_sub.add_parser("add")
    artifact_add.add_argument("--project")
    artifact_add.add_argument("--title", required=True)
    artifact_add.add_argument("--type", default="other", dest="artifact_type")
    artifact_add.add_argument("--summary")
    artifact_add.add_argument("--content")
    artifact_add.add_argument("--file-path")
    artifact_add.add_argument("--version")
    artifact_add.add_argument("--status", default="active")

    decision = sub.add_parser("decision")
    decision_sub = decision.add_subparsers(dest="decision_command", required=True)
    decision_add = decision_sub.add_parser("add")
    decision_add.add_argument("--project")
    decision_add.add_argument("--title", required=True)
    decision_add.add_argument("--decision", required=True)
    decision_add.add_argument("--reason")
    decision_add.add_argument("--alternatives")
    decision_add.add_argument("--impact")
    decision_add.add_argument("--status", default="active")

    context = sub.add_parser("context")
    context_sub = context.add_subparsers(dest="context_command", required=True)
    context_add = context_sub.add_parser("add")
    context_add.add_argument("--project")
    context_add.add_argument("--content", required=True)
    context_add.add_argument("--type", default="background", dest="context_type")
    context_add.add_argument("--importance", default="medium")
    context_add.add_argument("--status", default="active")

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    task_add = task_sub.add_parser("add")
    task_add.add_argument("--project")
    task_add.add_argument("--title", required=True)
    task_add.add_argument("--description")
    task_add.add_argument("--status", default="todo")
    task_add.add_argument("--priority", default="medium")
    task_add.add_argument("--due-date")

    session = sub.add_parser("session")
    session_sub = session.add_subparsers(dest="session_command", required=True)
    session_add = session_sub.add_parser("add")
    session_add.add_argument("--project")
    session_add.add_argument("--title")
    session_add.add_argument("--summary")
    session_add.add_argument("--raw-text")

    relation = sub.add_parser("relation")
    relation_sub = relation.add_subparsers(dest="relation_command", required=True)
    relation_add = relation_sub.add_parser("add")
    relation_add.add_argument("--source", required=True)
    relation_add.add_argument("--relation", required=True)
    relation_add.add_argument("--target", required=True)
    relation_add.add_argument("--weight", type=float, default=1.0)
    relation_add.add_argument("--note")
    relation_show = relation_sub.add_parser("show")
    relation_show.add_argument("ref")
    relation_show.add_argument("--depth", type=int, default=1)

    search_parser = sub.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--project")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    recall = sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--project")
    recall.add_argument("--top-k", type=int, default=10)
    recall.add_argument("--depth", type=int, default=1)
    recall.add_argument("--format", choices=["markdown", "json", "yaml"], default="markdown")

    context_pack = sub.add_parser("context-pack")
    context_pack.add_argument("--project")
    context_pack.add_argument("--format", choices=["markdown", "json", "yaml"], default="markdown")

    this = sub.add_parser("this", help="Rule-extract and auto-save current text")
    this.add_argument("--text")
    this.add_argument("--file")
    this.add_argument("--project")
    this.add_argument("--dry-run", action="store_true")

    capture = sub.add_parser("capture", help="Legacy alias for track this")
    capture.add_argument("--project")
    capture.add_argument("--text")
    capture.add_argument("--file")
    capture.add_argument("--dry-run", action="store_true")
    capture.add_argument("--format", choices=["json"], default="json")

    save = sub.add_parser("save")
    save.add_argument("--include")
    save.add_argument("--all", action="store_true", dest="save_all")

    save_candidates = sub.add_parser("save-candidates")
    save_candidates.add_argument("path")
    save_candidates.add_argument("--all", action="store_true", dest="save_all")
    save_candidates.add_argument("--include")

    file_parser = sub.add_parser("file")
    file_parser.add_argument("--path")
    file_parser.add_argument("--title")
    file_parser.add_argument("--type", default="other", dest="artifact_type")
    file_parser.add_argument("--summary")
    file_parser.add_argument("--project")

    import_parser = sub.add_parser("import")
    import_sub = import_parser.add_subparsers(dest="import_command", required=True)
    import_file_parser = import_sub.add_parser("file")
    import_file_parser.add_argument("--path", required=True)
    import_file_parser.add_argument("--type")
    import_file_parser.add_argument("--project")
    import_folder_parser = import_sub.add_parser("folder")
    import_folder_parser.add_argument("--path", required=True)
    import_folder_parser.add_argument("--recursive", action="store_true")
    import_folder_parser.add_argument("--project")
    import_text_parser = import_sub.add_parser("text")
    import_text_parser.add_argument("--title", required=True)
    import_text_parser.add_argument("--text", required=True)
    import_text_parser.add_argument("--type", default="chat_log")
    import_text_parser.add_argument("--project")

    backfill = sub.add_parser("backfill")
    backfill.add_argument("action", nargs="?", default="start", choices=["start", "extract", "review", "save", "complete"])
    backfill.add_argument("--project")

    cost = sub.add_parser("cost")
    cost.add_argument("action", nargs="?", default="status", choices=["status", "mode", "logs", "estimate"])
    cost.add_argument("value", nargs="?")

    return parser


def normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    first_index = 0
    while first_index < len(argv) and argv[first_index].startswith("--"):
        first_index += 2 if first_index + 1 < len(argv) else 1
    if first_index >= len(argv):
        return argv
    first = argv[first_index]
    if first == "查":
        query = " ".join(argv[first_index + 1 :])
        return argv[:first_index] + ["recall", query]
    if first == "pack":
        return argv[:first_index] + ["context-pack"]
    if first not in KNOWN_COMMANDS and not first.startswith("-"):
        return argv[:first_index] + ["project", "enter", first] + argv[first_index + 1 :]
    return argv


def main(argv: list[str] | None = None) -> int:
    argv = normalize_argv(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            db_path = init_db(args.db)
            config_path = init_config()
            print(f"Initialized Track database at {db_path}")
            print(f"Initialized Track config at {config_path}")
            return 0

        init_db(args.db)
        init_config()
        with connect(args.db) as conn:
            result = dispatch(conn, args)
            if result is not None:
                print(result)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def dispatch(conn, args) -> str | None:
    if args.command == "project":
        if args.project_command == "enter":
            project, created = enter_project(conn, args.name)
            set_current_project(project["name"])
            heading = "Created and entered" if created else "Entered"
            return f"{heading} project: {project['name']}\n\n" + render_track_pack(conn, project["name"], "markdown")
        if args.project_command == "create":
            item = create_project(conn, args.name, args.description, args.goal, args.status, args.stage, args.summary)
            set_current_project(item["name"])
            return project_card(item)
        if args.project_command == "show":
            item = get_project(conn, args.project)
            if not item:
                raise ValueError(f"Project not found: {args.project}")
            return project_card(item)
        if args.project_command == "list":
            items = list_projects(conn)
            return "\n".join(f"- {x['name']} [{x['status']}] {x.get('current_stage') or ''}".rstrip() for x in items) or "_No projects._"
        if args.project_command == "update-summary":
            item = update_project_summary(conn, args.project, args.summary)
            return project_card(item)

    if args.command == "question":
        project = resolve_project(args.project)
        item = create_question(conn, project, args.title, args.text, args.summary, args.status, args.question_type, args.importance)
        return created("question", item)

    if args.command == "answer":
        project = resolve_project(args.project)
        item = create_answer(conn, project, args.summary, args.question, args.detail, args.confidence, args.status)
        return created("answer", item)

    if args.command == "artifact":
        project = resolve_project(args.project)
        item = create_artifact(conn, project, args.title, args.artifact_type, args.summary, args.content, args.file_path, args.version, args.status)
        return created("artifact", item)

    if args.command == "decision":
        project = resolve_project(args.project)
        item = create_decision(conn, project, args.title, args.decision, args.reason, args.alternatives, args.impact, args.status)
        return created("decision", item)

    if args.command == "context":
        project = resolve_project(args.project)
        item = create_context(conn, project, args.content, args.context_type, args.importance, args.status)
        return created("context", item)

    if args.command == "task":
        project = resolve_project(args.project)
        item = create_task(conn, project, args.title, args.description, args.status, args.priority, args.due_date)
        return created("task", item)

    if args.command == "session":
        project = resolve_project(args.project)
        item = create_session(conn, project, args.title, args.summary, args.raw_text)
        return created("session", item)

    if args.command == "relation":
        if args.relation_command == "add":
            source_type, source_id = parse_ref(args.source)
            target_type, target_id = parse_ref(args.target)
            item = add_relation(conn, source_type, source_id, args.relation, target_type, target_id, args.weight, args.note)
            return created("relation", item)
        if args.relation_command == "show":
            entity_type, entity_id = parse_ref(args.ref)
            return json_output(get_relations_for(conn, entity_type, entity_id, args.depth))

    if args.command == "search":
        project_id = project_id_for(conn, args.project)
        rows = search(conn, args.query, project_id, args.limit)
        return json_output(rows) if args.format == "json" else render_search(rows)

    if args.command == "recall":
        project = args.project or get_current_project()
        pack = build_recall_context_pack(conn, args.query, project, args.top_k, args.depth)
        text = render_context_pack(pack, args.format)
        return text if args.format != "markdown" else enforce_context_limit(text)[0]

    if args.command == "context-pack":
        return render_track_pack(conn, resolve_project(args.project), args.format)

    if args.command in {"this", "capture"}:
        project = resolve_project(args.project)
        text = text_from_args(args)
        candidates = capture_candidates(project, text)
        write_latest_candidates(candidates)
        if getattr(args, "dry_run", False):
            return json_output(candidates)
        saved = save_candidates_data(conn, candidates, groups=None)
        return json_output({"auto_saved": saved, "candidates": candidates})

    if args.command == "save":
        data = read_json(LATEST_CANDIDATES_PATH)
        return json_output({"saved": save_candidates_data(conn, data, groups=groups_from_args(args.save_all, args.include))})

    if args.command == "save-candidates":
        data = read_json(args.path)
        return json_output({"saved": save_candidates_data(conn, data, groups=groups_from_args(args.save_all, args.include))})

    if args.command == "file":
        project = resolve_project(args.project)
        title, summary, path = artifact_from_file_args(args)
        item = create_artifact(conn, project, title, args.artifact_type, summary, file_path=path)
        return created("artifact", item)

    if args.command == "import":
        project = resolve_project(getattr(args, "project", None))
        if args.import_command == "file":
            return json_output(import_file(conn, project, args.path, args.type))
        if args.import_command == "folder":
            return json_output({"imported": import_folder(conn, project, args.path, args.recursive)})
        if args.import_command == "text":
            return json_output(import_text(conn, project, args.title, args.text, args.type))

    if args.command == "backfill":
        project = resolve_project(args.project)
        if args.action == "start":
            return project_card(start_backfill(conn, project))
        if args.action == "extract":
            candidates = extract_from_sources(conn, project)
            write_latest_candidates(candidates)
            saved = save_candidates_data(conn, candidates, groups=None)
            return json_output({"auto_saved": saved, "candidates": candidates})
        if args.action == "review":
            return json_output(review_backfill(conn, project))
        if args.action == "save":
            data = read_json(LATEST_CANDIDATES_PATH)
            return json_output({"saved": save_candidates_data(conn, data, groups=None)})
        if args.action == "complete":
            return project_card(complete_backfill(conn, project))

    if args.command == "cost":
        if args.action == "status":
            return simple_yaml({"cost_guard": cost_status()})
        if args.action == "mode":
            if not args.value:
                raise ValueError("Usage: track cost mode local_only|strict_budget")
            return simple_yaml({"cost_guard": update_mode(args.value)})
        if args.action == "logs":
            return json_output(list_ai_logs(conn))
        if args.action == "estimate":
            if not args.value:
                raise ValueError("Usage: track cost estimate TEXT")
            return simple_yaml({"estimate": {"input_text": args.value, "tokens": estimate_tokens(args.value)}})

    raise ValueError(f"Unsupported command: {args.command}")


def resolve_project(project: str | None) -> str:
    current = project or get_current_project()
    if not current:
        raise ValueError("No current project. Run `track PROJECT_NAME` first, or pass --project.")
    return current


def project_id_for(conn, project: str | None) -> str | None:
    if not project:
        current = get_current_project()
        project = current
    if not project:
        return None
    row = get_project(conn, project)
    if not row:
        raise ValueError(f"Project not found: {project}")
    return row["id"]


def render_track_pack(conn, project: str, output_format: str) -> str:
    text = render_context_pack(build_project_context_pack(conn, project), output_format)
    return text if output_format != "markdown" else enforce_context_limit(text)[0]


def text_from_args(args) -> str:
    if getattr(args, "text", None):
        return args.text
    if getattr(args, "file", None):
        return Path(args.file).expanduser().read_text(encoding="utf-8", errors="replace")
    raise ValueError("Use --text or --file.")


def write_latest_candidates(data: dict) -> None:
    LATEST_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_CANDIDATES_PATH.write_text(json_output(data), encoding="utf-8")


def groups_from_args(save_all: bool, include: str | None) -> set[str] | None:
    if save_all or not include:
        return None
    return {x.strip() for x in include.split(",") if x.strip()}


def save_candidates_data(conn, data: dict, groups: set[str] | None = None) -> dict:
    if "project" not in data and "candidates" in data and isinstance(data["candidates"], dict) and "project" in data["candidates"]:
        data = data["candidates"]
    project = data["project"]
    candidates = data.get("candidates", {})
    active_groups = groups or set(candidates.keys())
    saved: dict[str, list[str]] = {group: [] for group in active_groups}
    for item in candidates.get("questions", []) if "questions" in active_groups else []:
        row = create_question(
            conn,
            project,
            item["title"],
            item.get("original_text"),
            item.get("summary"),
            item.get("status", "open"),
            item.get("question_type", "unknown"),
            item.get("importance_score", 0.5),
            item.get("confidence", "medium"),
            item.get("extraction_method", "keyword_rule"),
            item.get("source_material_id"),
        )
        saved.setdefault("questions", []).append(row["id"])
    for item in candidates.get("decisions", []) if "decisions" in active_groups else []:
        row = create_decision(
            conn,
            project,
            item["title"],
            item["decision"],
            item.get("reason"),
            status=item.get("status", "active"),
            confidence=item.get("confidence", "medium"),
            extraction_method=item.get("extraction_method", "keyword_rule"),
            source_material_id=item.get("source_material_id"),
        )
        saved.setdefault("decisions", []).append(row["id"])
    for item in candidates.get("artifacts", []) if "artifacts" in active_groups else []:
        row = create_artifact(
            conn,
            project,
            item["title"],
            item.get("artifact_type", "other"),
            item.get("summary"),
            status=item.get("status", "active"),
            confidence=item.get("confidence", "medium"),
            extraction_method=item.get("extraction_method", "keyword_rule"),
            source_material_id=item.get("source_material_id"),
        )
        saved.setdefault("artifacts", []).append(row["id"])
    for item in candidates.get("contexts", []) if "contexts" in active_groups else []:
        row = create_context(
            conn,
            project,
            item["content"],
            item.get("context_type", "background"),
            item.get("importance", "medium"),
            item.get("status", "active"),
            item.get("confidence", "medium"),
            item.get("extraction_method", "keyword_rule"),
            item.get("source_material_id"),
        )
        saved.setdefault("contexts", []).append(row["id"])
    for item in candidates.get("tasks", []) if "tasks" in active_groups else []:
        row = create_task(
            conn,
            project,
            item["title"],
            item.get("description"),
            item.get("status", "todo"),
            item.get("priority", "medium"),
            confidence=item.get("confidence", "medium"),
            extraction_method=item.get("extraction_method", "keyword_rule"),
            source_material_id=item.get("source_material_id"),
        )
        saved.setdefault("tasks", []).append(row["id"])
    return saved


def artifact_from_file_args(args) -> tuple[str, str | None, str | None]:
    if args.path:
        path = Path(args.path).expanduser()
        if not path.exists():
            raise ValueError(f"File not found: {args.path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        title = args.title or path.name
        summary = args.summary or " ".join(text.split())[:240]
        return title, summary, str(path)
    if not args.title:
        raise ValueError("Use --path or --title.")
    return args.title, args.summary, None


def project_card(item: dict) -> str:
    return "\n".join(
        [
            f"# {item['name']}",
            "",
            f"ID: {item['id']}",
            "",
            "Goal:",
            item.get("goal") or "_None._",
            "",
            "Stage:",
            item.get("current_stage") or "_None._",
            "",
            "Hot Summary:",
            item.get("hot_summary") or "_None._",
            "",
            "Backfill:",
            item.get("backfill_status") or "not_started",
        ]
    )


def created(entity_type: str, item: dict) -> str:
    label = item.get("title") or item.get("name") or item.get("summary") or item.get("content") or item["id"]
    return f"Created {entity_type}: {item['id']}\n{label}"


def render_search(rows: list[dict]) -> str:
    lines = ["# Search Results", ""]
    if not rows:
        lines.append("_No matches._")
        return "\n".join(lines)
    for row in rows:
        title = row.get("title") or row.get("body", "").splitlines()[0:1] or ""
        if isinstance(title, list):
            title = title[0] if title else ""
        lines.append(f"- {row['entity_type']}:{row['entity_id']} - {title}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
