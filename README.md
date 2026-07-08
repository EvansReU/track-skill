# Track

语言 / Language: [中文](#中文) | [English](#english)

## 中文

Track 是一个本地优先的项目记忆追踪器，面向 AI 辅助项目工作。它把问题、答案、决策、产出物、上下文、任务、阶段摘要和历史材料保存在 SQLite 中，并通过本地搜索和关系查询生成小型 Track Pack。

> 每天使用 `track`，但不会意外消耗 AI token。

### 核心原则

- **默认 0 token：** 不调用云端 AI，不做 embedding，不后台总结。
- **本地优先：** 数据保存在 `~/.track/track.sqlite`。
- **小包召回：** 默认返回摘要和元数据，而不是完整历史。
- **规则自动保存：** 本地关键词提取不消耗 token，所以 `track this` 会自动保存提取节点。
- **置信度可见：** 自动提取节点会标记 `confidence=medium` 和 `extraction_method=keyword_rule`。
- **AI 受保护：** 未来 AI 命令必须使用 `ai-*` 前缀，并通过 Cost Guard。

### 为什么叫 Track

用户只需要记住一个词：`track`。它不是复杂知识库，也不是默认自动分析系统，而是每天都能轻量使用的项目追踪口令。

最常用的 4 个命令：

```bash
track PROJECT_NAME
track this --text "当前讨论内容..."
track 查 keyword
track pack
```

### 安装

```bash
python3 -m pip install -e .
```

安装后会有两个命令：

- `track`：主命令
- `pmg`：早期 Project Memory Graph MVP 的兼容别名

### 在 Codex 中启用 Skill

如果希望在 Codex 里直接输入 `track` 就调用本工具，而不是被理解成“重新做一个 Track”或 git track，请安装仓库里的 Codex Skill：

```bash
mkdir -p ~/.codex/skills
cp -R codex-skill/track ~/.codex/skills/track
```

安装后开启新的 Codex 线程或重启 Codex，让 Skill 列表重新加载。之后：

```text
track
track this
track 查 token消耗
track pack
```

都会触发本地 Track CLI。

### 初始化

```bash
track init
```

会创建：

- `~/.track/track.sqlite`
- `~/.track/config.yaml`
- `~/.track/current_project`
- `~/.track/candidates/latest_candidates.json`

测试时可指定数据库：

```bash
track --db /tmp/track.sqlite init
```

### 进入或创建项目

```bash
track history-track
```

如果项目不存在，Track 会创建它；如果已存在，Track 会进入该项目并保存为当前项目。

等价完整命令：

```bash
track project enter history-track
```

### 记录当前讨论

```bash
track this --text "这个 Skill 的指令复杂，应该简化成 track 一个核心口令。需要实现 Cost Guard。"
```

规则提取是本地执行且 0 token，所以 Track 会自动保存提取出的记录。最新提取结果也会写入：

```text
~/.track/candidates/latest_candidates.json
```

只预览不保存：

```bash
track this --text "..." --dry-run
track this --file ./current_session.txt --dry-run
```

兼容旧命令：

```bash
track capture --project history-track --text "..."
```

### 搜索与召回

```bash
track 查 token消耗
track recall "token消耗"
```

Track 会搜索当前项目，沿关系查询附近节点，并返回受限的 Track Pack。默认不输出 artifact 全文、source material 原文或 session 原文。

### 生成项目包

```bash
track pack
track context-pack
```

项目包包含目标、热摘要、有效决策、未解决问题、当前产出物、开放任务和可见置信度。

JSON 和 YAML 输出：

```bash
track pack --format json
track recall "token" --format yaml
```

### 手动添加结构化记录

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

### 关系

```bash
track relation add \
  --source decision:decision_默认不读取全量历史 \
  --relation related_to \
  --target question:q_项目庞大时如何控制-token-消耗 \
  --note "该决策回答 token 消耗问题。"

track relation show question:q_项目庞大时如何控制-token-消耗
```

支持的关系类型包括 `belongs_to`, `triggered_by`, `answers`, `answered_by`, `derived_from`, `depends_on`, `related_to`, `produced`, `mentions` 等。

### 保存产出物

保存文件为 artifact：

```bash
track file --path ./handoff.md
```

直接保存元数据：

```bash
track file \
  --title "Track Skill 完整开发交接文档" \
  --type handoff_doc \
  --summary "给 Codex 实现 Track MVP 的交接文档。"
```

Track 默认保存 metadata 和 summary，不会把文件内容发送给 AI。

### 导入历史材料

```bash
track import file --path ./old-notes.md
track import folder --path ./docs --recursive
track import text --title "历史对话" --type chat_log --text "..."
```

MVP 支持文件类型：

- `.md`
- `.txt`
- `.json`
- `.py`

导入的材料会保存为 `source_materials`，初始状态为 `processed_status=pending`。

### 补录已有项目

```bash
track old-project
track backfill
track import folder --path ./old_project_docs --recursive
track backfill extract
track backfill review
track backfill complete
track pack
```

Backfill 使用和 `track this` 相同的本地规则，自动保存提取节点，并标记 source material ID、confidence 和 extraction method。它不会调用 AI。

### Cost Guard

```bash
track cost
track cost status
track cost mode local_only
track cost mode strict_budget
track cost estimate "token 消耗"
track cost logs
```

默认配置：

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

MVP 中 AI 命令刻意不启用。未来所有 AI 命令必须使用类似下面的命名，并经过成本确认：

```bash
track ai-summarize artifact_001 --confirm-cost
track ai-extract source_001 --confirm-cost
```

非 `ai-*` 命令都是本地命令。

### 测试

```bash
python3 -m unittest discover -s tests -q
```

### MVP 限制

- 不做云端同步。
- 不做多人协作。
- 不做 Web UI。
- 不自动读取 ChatGPT 历史。
- 不做向量检索。
- 不做默认 AI 总结。
- 不做默认全文 AI 分析。

### 路线图

- 显式确认的可选 `ai-*` 命令。
- 本地向量检索。
- Web UI。
- 图谱可视化。
- 时间线生成。
- 冲突检测。

## English

Track is a local-first project memory tracker for AI-assisted work. It stores questions, answers, decisions, artifacts, context, tasks, sessions, and historical source materials in SQLite, then recalls small structured Track Packs through local search and relation lookup.

> Use `track` every day without accidentally spending AI tokens.

### Core Principles

- **Default 0 token:** no cloud AI calls, embeddings, or background summarization.
- **Local first:** data lives in `~/.track/track.sqlite`.
- **Small packs:** recall returns summaries and metadata by default, not full history.
- **Rules auto-save:** local keyword extraction costs 0 tokens, so `track this` saves extracted nodes automatically.
- **Visible confidence:** auto-extracted nodes are marked `confidence=medium` and `extraction_method=keyword_rule`.
- **Guarded AI:** future AI commands must use an `ai-*` prefix and pass Cost Guard checks.

### Why “Track”

The user should only need to remember one word: `track`. It is not a heavy knowledge base or an always-on AI analyzer. It is a lightweight project tracking command for daily use.

Four daily commands:

```bash
track PROJECT_NAME
track this --text "current discussion..."
track 查 keyword
track pack
```

### Install

```bash
python3 -m pip install -e .
```

This installs two command names:

- `track`: primary CLI
- `pmg`: compatibility alias for the earlier Project Memory Graph MVP

### Enable The Codex Skill

To make Codex treat `track` as this local tool instead of a request to rebuild Track or a git tracking command, install the bundled Codex Skill:

```bash
mkdir -p ~/.codex/skills
cp -R codex-skill/track ~/.codex/skills/track
```

Then start a new Codex thread or restart Codex so the skill list reloads. After that, prompts like these should call the local Track CLI:

```text
track
track this
track 查 token消耗
track pack
```

### Initialize

```bash
track init
```

This creates:

- `~/.track/track.sqlite`
- `~/.track/config.yaml`
- `~/.track/current_project`
- `~/.track/candidates/latest_candidates.json`

Use another database for testing:

```bash
track --db /tmp/track.sqlite init
```

### Enter Or Create A Project

```bash
track history-track
```

If the project does not exist, Track creates it. If it exists, Track enters it and stores it as the current project.

Equivalent full command:

```bash
track project enter history-track
```

### Record Current Discussion

```bash
track this --text "The CLI is too complex. It should be simplified into one core command: track."
```

Rule extraction is local and costs 0 tokens, so Track automatically saves extracted records. The latest extraction payload is also written to:

```text
~/.track/candidates/latest_candidates.json
```

Preview without saving:

```bash
track this --text "..." --dry-run
track this --file ./current_session.txt --dry-run
```

Legacy equivalent:

```bash
track capture --project history-track --text "..."
```

### Search And Recall

```bash
track 查 token-cost
track recall "token-cost"
```

Track searches the current project, follows nearby relations, and returns a bounded Track Pack. It does not output artifact full text, raw source material, or raw session logs by default.

### Generate A Project Pack

```bash
track pack
track context-pack
```

The pack includes project goal, hot summary, active decisions, open questions, active artifacts, open tasks, and visible confidence.

JSON and YAML output:

```bash
track pack --format json
track recall "token" --format yaml
```

### Add Structured Records Manually

```bash
track question add --title "How should large projects control token cost?" --summary "Use top-k Track Packs to control context size."

track decision add \
  --title "Do not load full history by default" \
  --decision "Recall only relevant context packs instead of reading the full project history." \
  --reason "Reduce token cost and keep context clean."

track artifact add \
  --title "Track Skill handoff document" \
  --type handoff_doc \
  --summary "A handoff document for implementing the Track MVP."

track context add \
  --content "Track should be local-first and default to 0 token cost." \
  --type constraint \
  --importance high

track task add --title "Implement Backfill Mode" --priority high
```

### Relations

```bash
track relation add \
  --source decision:decision_do-not-load-full-history-by-default \
  --relation related_to \
  --target question:q_how-should-large-projects-control-token-cost \
  --note "This decision answers the token-cost question."

track relation show question:q_how-should-large-projects-control-token-cost
```

Supported relation types include `belongs_to`, `triggered_by`, `answers`, `answered_by`, `derived_from`, `depends_on`, `related_to`, `produced`, `mentions`, and others.

### Save Artifacts

Save a generated file as an artifact:

```bash
track file --path ./handoff.md
```

Save metadata directly:

```bash
track file \
  --title "Track Skill handoff document" \
  --type handoff_doc \
  --summary "A handoff document for implementing the Track MVP."
```

Track stores metadata and summary by default. It does not send file content to AI.

### Import Historical Material

```bash
track import file --path ./old-notes.md
track import folder --path ./docs --recursive
track import text --title "Historical conversation" --type chat_log --text "..."
```

Supported MVP file types:

- `.md`
- `.txt`
- `.json`
- `.py`

Imported material is stored as `source_materials` with `processed_status=pending`.

### Backfill Existing Projects

```bash
track old-project
track backfill
track import folder --path ./old_project_docs --recursive
track backfill extract
track backfill review
track backfill complete
track pack
```

Backfill extraction uses the same local rules as `track this`, auto-saves extracted nodes, and marks them with source material IDs, confidence, and extraction method. It does not call AI.

### Cost Guard

```bash
track cost
track cost status
track cost mode local_only
track cost mode strict_budget
track cost estimate "token cost"
track cost logs
```

Default config:

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

AI commands are intentionally not enabled in the MVP. Future AI commands must use names like these and pass explicit cost confirmation:

```bash
track ai-summarize artifact_001 --confirm-cost
track ai-extract source_001 --confirm-cost
```

Non-`ai-*` commands are local only.

### Test

```bash
python3 -m unittest discover -s tests -q
```

### MVP Limits

- No cloud sync.
- No multi-user collaboration.
- No web UI.
- No automatic ChatGPT history reading.
- No vector search.
- No default AI summarization.
- No automatic full-text AI analysis.

### Roadmap

- Optional `ai-*` commands with explicit confirmation.
- Local vector search.
- Web UI.
- Graph visualization.
- Timeline generation.
- Conflict detection.
