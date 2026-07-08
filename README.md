# Track

**中文**  
Track 是一个本地优先的项目记忆追踪器，面向 AI 辅助项目工作。它把问题、答案、决策、产出物、上下文、任务、阶段摘要和历史材料保存在 SQLite 中，并通过本地搜索和关系查询生成小型 Track Pack。

**English**  
Track is a local-first project memory tracker for AI-assisted work. It stores questions, answers, decisions, artifacts, context, tasks, sessions, and historical source materials in SQLite, then recalls small structured Track Packs through local search and relation lookup.

**核心承诺 / Core Promise**

> 每天使用 `track`，但不会意外消耗 AI token.  
> Use `track` every day without accidentally spending AI tokens.

## 核心原则 / Core Principles

- **默认 0 token / Default 0 token:** 不调用云端 AI，不做 embedding，不后台总结。No cloud AI calls, embeddings, or background summarization.
- **本地优先 / Local first:** 数据保存在 `~/.track/track.sqlite`. Data lives in `~/.track/track.sqlite`.
- **小包召回 / Small packs:** 默认返回摘要和元数据，而不是完整历史。Recall returns summaries and metadata by default, not full history.
- **规则自动保存 / Rules auto-save:** 本地关键词提取不消耗 token，所以 `track this` 会自动保存提取节点。Local keyword extraction costs 0 tokens, so `track this` saves extracted nodes automatically.
- **置信度可见 / Visible confidence:** 自动提取节点会标记 `confidence=medium` 和 `extraction_method=keyword_rule`. Auto-extracted nodes are marked clearly.
- **AI 受保护 / Guarded AI:** 未来 AI 命令必须使用 `ai-*` 前缀，并通过 Cost Guard。Future AI commands must use an `ai-*` prefix and pass Cost Guard checks.

## 为什么叫 Track / Why “Track”

**中文**  
用户只需要记住一个词：`track`。它不是复杂知识库，也不是默认自动分析系统，而是每天都能轻量使用的项目追踪口令。

**English**  
The user should only need to remember one word: `track`. It is not a heavy knowledge base or an always-on AI analyzer. It is a lightweight project tracking command for daily use.

最常用的 4 个命令 / Four daily commands:

```bash
track PROJECT_NAME
track this --text "current discussion..."
track 查 keyword
track pack
```

## 安装 / Install

```bash
python3 -m pip install -e .
```

安装后会有两个命令 / This installs two command names:

- `track`: 主命令 / primary CLI
- `pmg`: 早期 Project Memory Graph MVP 的兼容别名 / compatibility alias

## 初始化 / Initialize

```bash
track init
```

会创建 / This creates:

- `~/.track/track.sqlite`
- `~/.track/config.yaml`
- `~/.track/current_project`
- `~/.track/candidates/latest_candidates.json`

测试时可指定数据库 / Use another database for testing:

```bash
track --db /tmp/track.sqlite init
```

## 进入或创建项目 / Enter Or Create A Project

```bash
track history-track
```

**中文**  
如果项目不存在，Track 会创建它；如果已存在，Track 会进入该项目并保存为当前项目。

**English**  
If the project does not exist, Track creates it. If it exists, Track enters it and stores it as the current project.

等价完整命令 / Equivalent full command:

```bash
track project enter history-track
```

## 记录当前讨论 / Record Current Discussion

```bash
track this --text "这个 Skill 的指令复杂，应该简化成 track 一个核心口令。需要实现 Cost Guard。"
```

**中文**  
规则提取是本地执行且 0 token，所以 Track 会自动保存提取出的记录。最新提取结果也会写入：

**English**  
Rule extraction is local and costs 0 tokens, so Track automatically saves extracted records. The latest extraction payload is also written to:

```text
~/.track/candidates/latest_candidates.json
```

只预览不保存 / Preview without saving:

```bash
track this --text "..." --dry-run
track this --file ./current_session.txt --dry-run
```

兼容旧命令 / Legacy equivalent:

```bash
track capture --project history-track --text "..."
```

## 搜索与召回 / Search And Recall

```bash
track 查 token消耗
track recall "token消耗"
```

**中文**  
Track 会搜索当前项目，沿关系查询附近节点，并返回受限的 Track Pack。默认不输出 artifact 全文、source material 原文或 session 原文。

**English**  
Track searches the current project, follows nearby relations, and returns a bounded Track Pack. It does not output artifact full text, raw source material, or raw session logs by default.

## 生成项目包 / Generate A Project Pack

```bash
track pack
track context-pack
```

**中文**  
项目包包含目标、热摘要、有效决策、未解决问题、当前产出物、开放任务和可见置信度。

**English**  
The pack includes project goal, hot summary, active decisions, open questions, active artifacts, open tasks, and visible confidence.

JSON 和 YAML 输出 / JSON and YAML output:

```bash
track pack --format json
track recall "token" --format yaml
```

## 手动添加结构化记录 / Add Structured Records Manually

```bash
track question add --title "项目庞大时如何控制 token 消耗？" --summary "用 top-k Track Pack 控制上下文大小。"

track decision add \
  --title "默认不读取全量历史" \
  --decision "只召回相关上下文包，而不是读取完整项目历史。" \
  --reason "降低 token 成本并保持上下文干净。"

track artifact add \
  --title "Track Skill 完整开发交接文档" \
  --type handoff_doc \
  --summary "给 Codex 实现 Track MVP 的交接文档。"

track context add \
  --content "用户希望 Track 默认 0 token，本地优先。" \
  --type constraint \
  --importance high

track task add --title "实现 Backfill Mode" --priority high
```

## 关系 / Relations

```bash
track relation add \
  --source decision:decision_默认不读取全量历史 \
  --relation related_to \
  --target question:q_项目庞大时如何控制-token-消耗 \
  --note "该决策回答 token 消耗问题。"

track relation show question:q_项目庞大时如何控制-token-消耗
```

**中文**  
支持的关系类型包括 `belongs_to`, `triggered_by`, `answers`, `answered_by`, `derived_from`, `depends_on`, `related_to`, `produced`, `mentions` 等。

**English**  
Supported relation types include `belongs_to`, `triggered_by`, `answers`, `answered_by`, `derived_from`, `depends_on`, `related_to`, `produced`, `mentions`, and others.

## 保存产出物 / Save Artifacts

保存文件为 artifact / Save a generated file as an artifact:

```bash
track file --path ./handoff.md
```

直接保存元数据 / Save metadata directly:

```bash
track file \
  --title "Track Skill 完整开发交接文档" \
  --type handoff_doc \
  --summary "给 Codex 实现 Track MVP 的交接文档。"
```

**中文**  
Track 默认保存 metadata 和 summary，不会把文件内容发送给 AI。

**English**  
Track stores metadata and summary by default. It does not send file content to AI.

## 导入历史材料 / Import Historical Material

```bash
track import file --path ./old-notes.md
track import folder --path ./docs --recursive
track import text --title "历史对话" --type chat_log --text "..."
```

MVP 支持文件类型 / Supported MVP file types:

- `.md`
- `.txt`
- `.json`
- `.py`

**中文**  
导入的材料会保存为 `source_materials`，初始状态为 `processed_status=pending`。

**English**  
Imported material is stored as `source_materials` with `processed_status=pending`.

## 补录已有项目 / Backfill Existing Projects

```bash
track old-project
track backfill
track import folder --path ./old_project_docs --recursive
track backfill extract
track backfill review
track backfill complete
track pack
```

**中文**  
Backfill 使用和 `track this` 相同的本地规则，自动保存提取节点，并标记 source material ID、confidence 和 extraction method。它不会调用 AI。

**English**  
Backfill extraction uses the same local rules as `track this`, auto-saves extracted nodes, and marks them with source material IDs, confidence, and extraction method. It does not call AI.

## Cost Guard

```bash
track cost
track cost status
track cost mode local_only
track cost mode strict_budget
track cost estimate "token 消耗"
track cost logs
```

默认配置 / Default config:

```yaml
cost_guard:
  mode: local_only
  ai_auto_call: false
  allow_fulltext_ai: false
  require_cost_confirmation: true
  max_context_pack_chars: 6000
  include_artifact_content_by_default: false
  include_source_material_raw_text_by_default: false
  include_session_raw_text_by_default: false
```

**中文**  
MVP 中 AI 命令刻意不启用。未来所有 AI 命令必须使用类似下面的命名，并经过成本确认：

**English**  
AI commands are intentionally not enabled in the MVP. Future AI commands must use names like these and pass explicit cost confirmation:

```bash
track ai-summarize artifact_001 --confirm-cost
track ai-extract source_001 --confirm-cost
```

非 `ai-*` 命令都是本地命令。  
Non-`ai-*` commands are local only.

## 测试 / Test

```bash
python3 -m unittest discover -s tests -q
```

## MVP 限制 / MVP Limits

- 不做云端同步 / No cloud sync.
- 不做多人协作 / No multi-user collaboration.
- 不做 Web UI / No web UI.
- 不自动读取 ChatGPT 历史 / No automatic ChatGPT history reading.
- 不做向量检索 / No vector search.
- 不做默认 AI 总结 / No default AI summarization.
- 不做默认全文 AI 分析 / No automatic full-text AI analysis.

## 路线图 / Roadmap

- 显式确认的可选 `ai-*` 命令 / Optional `ai-*` commands with explicit confirmation.
- 本地向量检索 / Local vector search.
- Web UI.
- 图谱可视化 / Graph visualization.
- 时间线生成 / Timeline generation.
- 冲突检测 / Conflict detection.
