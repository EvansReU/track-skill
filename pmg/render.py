from __future__ import annotations

import json


def json_output(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def simple_yaml(data: object, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(simple_yaml(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {format_scalar(value)}")
        return "\n".join(line for line in lines if line != "")
    if isinstance(data, list):
        if not data:
            return f"{pad}[]"
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(simple_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {format_scalar(item)}")
        return "\n".join(lines)
    return f"{pad}{format_scalar(data)}"


def format_scalar(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if "\n" in text or text.startswith(("{", "[", "-", "#")):
        return json.dumps(text, ensure_ascii=False)
    return text


def render_items(title: str, items: list[dict], formatter) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("_None._")
    else:
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {formatter(item)}")
    lines.append("")
    return lines
