from __future__ import annotations

import re


QUESTION_MARKERS = ("是否", "怎么", "如何", "要不要", "能不能", "为什么", "?")
DECISION_MARKERS = ("决定", "不做", "改成", "先做", "放弃", "MVP 阶段", "应该", "采用")
ARTIFACT_MARKERS = ("生成文档", "交接文档", "代码", "PRD", "报告", "Prompt", "产出物")
TASK_MARKERS = ("下一步", "待办", "需要实现", "先完成", "实现", "补测试")
CONTEXT_MARKERS = ("我希望", "我担心", "约束", "成本", "本地", "云端", "token")


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?])\s+|[；;\n]+", text.strip())
    return [part.strip(" 。") for part in parts if part.strip(" 。")]


def score(markers: tuple[str, ...], text: str, base: float = 0.35) -> float:
    value = base + sum(0.15 for marker in markers if marker in text)
    return round(min(value, 1.0), 2)


def question_title(sentence: str) -> str:
    if sentence.endswith(("?", "？")):
        return sentence
    if "token" in sentence or "成本" in sentence:
        return "项目庞大时如何控制 token 消耗？"
    if "手动" in sentence or "自动" in sentence:
        return "这个 Skill 是否完全依赖用户手动打点？"
    return sentence[:60] + ("？" if not sentence.endswith("？") else "")


def decision_title(sentence: str) -> str:
    if "候选" in sentence or "确认" in sentence:
        return "采用自动候选提取 + 用户确认机制"
    if "全部历史" in sentence or "上下文包" in sentence:
        return "大型项目不加载全量历史"
    if "MVP" in sentence:
        return "MVP 阶段确定实现范围"
    return sentence[:48]


def artifact_type(sentence: str) -> str:
    if "交接" in sentence:
        return "handoff_doc"
    if "PRD" in sentence:
        return "prd"
    if "代码" in sentence:
        return "code"
    if "Prompt" in sentence:
        return "prompt"
    if "报告" in sentence:
        return "report"
    if "文档" in sentence:
        return "document"
    return "other"


def capture_candidates(project: str, text: str) -> dict:
    candidates = {
        "questions": [],
        "decisions": [],
        "artifacts": [],
        "contexts": [],
        "tasks": [],
    }
    for sentence in split_sentences(text):
        if any(marker in sentence for marker in QUESTION_MARKERS):
            candidates["questions"].append(
                {
                    "title": question_title(sentence),
                    "original_text": sentence,
                    "summary": sentence,
                    "question_type": "unknown",
                    "status": "open",
                    "importance_score": score(QUESTION_MARKERS + CONTEXT_MARKERS, sentence),
                    "confidence": "medium",
                    "extraction_method": "keyword_rule",
                }
            )
        if any(marker in sentence for marker in DECISION_MARKERS):
            candidates["decisions"].append(
                {
                    "title": decision_title(sentence),
                    "decision": sentence,
                    "reason": "规则捕获：文本包含决策或范围选择信号。",
                    "status": "active",
                    "importance_score": score(DECISION_MARKERS, sentence, 0.45),
                    "confidence": "medium",
                    "extraction_method": "keyword_rule",
                }
            )
        if any(marker in sentence for marker in ARTIFACT_MARKERS):
            candidates["artifacts"].append(
                {
                    "title": sentence[:60],
                    "artifact_type": artifact_type(sentence),
                    "summary": sentence,
                    "status": "active",
                    "importance_score": score(ARTIFACT_MARKERS, sentence),
                    "confidence": "medium",
                    "extraction_method": "keyword_rule",
                }
            )
        if any(marker in sentence for marker in CONTEXT_MARKERS):
            candidates["contexts"].append(
                {
                    "content": sentence,
                    "context_type": "constraint" if any(k in sentence for k in ("约束", "成本", "本地", "云端", "token")) else "preference",
                    "importance": "high" if score(CONTEXT_MARKERS, sentence) >= 0.65 else "medium",
                    "status": "active",
                    "importance_score": score(CONTEXT_MARKERS, sentence),
                    "confidence": "medium",
                    "extraction_method": "keyword_rule",
                }
            )
        if any(marker in sentence for marker in TASK_MARKERS):
            candidates["tasks"].append(
                {
                    "title": sentence[:60],
                    "description": sentence,
                    "status": "todo",
                    "priority": "high" if "需要实现" in sentence or "先完成" in sentence else "medium",
                    "importance_score": score(TASK_MARKERS, sentence),
                    "confidence": "medium",
                    "extraction_method": "keyword_rule",
                }
            )
    return {"project": project, "candidates": candidates}
