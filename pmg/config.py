from __future__ import annotations

from pathlib import Path

from .db import DEFAULT_DATA_DIR


DEFAULT_CONFIG_PATH = DEFAULT_DATA_DIR / "config.yaml"
CURRENT_PROJECT_PATH = DEFAULT_DATA_DIR / "current_project"
LATEST_CANDIDATES_PATH = DEFAULT_DATA_DIR / "candidates" / "latest_candidates.json"

DEFAULT_CONFIG = {
    "cost_guard": {
        "mode": "local_only",
        "ai_auto_call": False,
        "allow_fulltext_ai": False,
        "require_cost_confirmation": True,
        "max_context_pack_chars": 6000,
        "max_context_pack_items": 25,
        "max_relation_depth": 2,
        "max_questions_per_pack": 5,
        "max_answers_per_pack": 5,
        "max_decisions_per_pack": 5,
        "max_artifacts_per_pack": 5,
        "max_contexts_per_pack": 5,
        "max_tasks_per_pack": 5,
        "max_ai_input_tokens_per_call": 4000,
        "max_ai_output_tokens_per_call": 1500,
        "max_ai_total_tokens_per_day": 20000,
        "include_artifact_content_by_default": False,
        "include_source_material_raw_text_by_default": False,
        "include_session_raw_text_by_default": False,
    },
    "runtime": {"current_project": None},
}


def init_config(config_path: str | Path | None = None) -> Path:
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "candidates").mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(to_yaml(DEFAULT_CONFIG), encoding="utf-8")
    return path


def read_config(config_path: str | Path | None = None) -> dict:
    path = init_config(config_path)
    return parse_simple_yaml(path.read_text(encoding="utf-8"))


def write_config(config: dict, config_path: str | Path | None = None) -> None:
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_yaml(config), encoding="utf-8")


def set_current_project(project_name: str) -> None:
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_PROJECT_PATH.write_text(project_name, encoding="utf-8")
    config = read_config()
    config.setdefault("runtime", {})["current_project"] = project_name
    write_config(config)


def get_current_project() -> str | None:
    if CURRENT_PROJECT_PATH.exists():
        value = CURRENT_PROJECT_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    return read_config().get("runtime", {}).get("current_project")


def set_cost_mode(mode: str) -> dict:
    if mode not in {"local_only", "strict_budget"}:
        raise ValueError("Cost mode must be local_only or strict_budget")
    config = read_config()
    config.setdefault("cost_guard", {})["mode"] = mode
    write_config(config)
    return config


def to_yaml(data: dict, indent: int = 0) -> str:
    lines = []
    pad = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.append(to_yaml(value, indent + 2).rstrip())
        elif isinstance(value, bool):
            lines.append(f"{pad}{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{pad}{key}: null")
        else:
            lines.append(f"{pad}{key}: {value}")
    return "\n".join(lines) + "\n"


def parse_simple_yaml(text: str) -> dict:
    result: dict = {}
    stack: list[tuple[int, dict]] = [(-1, result)]
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = raw.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_value(value)
    merged = DEFAULT_CONFIG.copy()
    deep_merge(merged, result)
    return merged


def parse_value(value: str):
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def deep_merge(base: dict, incoming: dict) -> None:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
