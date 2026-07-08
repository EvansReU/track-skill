# Track

Track is a local-first project memory tracker for AI-assisted work. It stores questions, answers, decisions, artifacts, context, tasks, sessions, and historical source materials in SQLite, then recalls small structured Track Packs through local search and relations.

The core promise is simple:

> Use `track` every day without accidentally spending AI tokens.

## Core Principles

- **Default 0 token:** no cloud AI calls, no embeddings, no background summarization.
- **Local first:** data lives in `~/.track/track.sqlite`.
- **Small packs, not full history:** recall returns summaries and metadata by default.
- **Rules auto-save:** local keyword extraction costs 0 tokens, so `track this` saves extracted nodes automatically.
- **Confidence is visible:** auto-extracted nodes are marked `confidence=medium` and `extraction_method=keyword_rule`.
- **AI is guarded:** future AI commands must use an `ai-*` prefix and pass Cost Guard checks.

## Why “Track”

The user should only need to remember one word: `track`.

Most daily use fits four commands:

```bash
track PROJECT_NAME
track this --text "current discussion..."
track 查 keyword
track pack
```

## Install

```bash
python3 -m pip install -e .
```

This installs two command names:

- `track`: the primary CLI
- `pmg`: compatibility alias for the earlier Project Memory Graph MVP

## Initialize

```bash
track init
```

This creates:

- `~/.track/track.sqlite`
- `~/.track/config.yaml`
- `~/.track/current_project`
- `~/.track/candidates/latest_candidates.json`

You can use another database for testing:

```bash
track --db /tmp/track.sqlite init
```

## Enter Or Create A Project

```bash
track history-track
```

If the project does not exist, Track creates it. If it exists, Track enters it and stores it as the current project.

Equivalent full command:

```bash
track project enter history-track
```

## Record Current Discussion

```bash
track this --text "这个 Skill 的指令复杂，应该简化成 track 一个核心口令。需要实现 Cost Guard。"
```

Because rule extraction is local and costs 0 tokens, Track automatically saves extracted records. It also writes the latest extraction payload to:

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

## Search And Recall

```bash
track 查 token消耗
track recall "token消耗"
```

Track searches the current project, follows nearby relations, and returns a bounded Track Pack. It does not output artifact full text, raw source material, or raw session logs by default.

## Generate A Project Pack

```bash
track pack
track context-pack
```

The pack includes project goal, hot summary, active decisions, open questions, active artifacts, open tasks, and visible confidence.

JSON and YAML are available:

```bash
track pack --format json
track recall "token" --format yaml
```

## Add Structured Records Manually

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

## Relations

```bash
track relation add \
  --source decision:decision_默认不读取全量历史 \
  --relation related_to \
  --target question:q_项目庞大时如何控制-token-消耗 \
  --note "该决策回答 token 消耗问题。"

track relation show question:q_项目庞大时如何控制-token-消耗
```

Supported relation types include `belongs_to`, `triggered_by`, `answers`, `answered_by`, `derived_from`, `depends_on`, `related_to`, `produced`, `mentions`, and others.

## Save Artifacts

Save a generated file as an artifact:

```bash
track file --path ./handoff.md
```

Or save metadata directly:

```bash
track file \
  --title "Track Skill 完整开发交接文档" \
  --type handoff_doc \
  --summary "给 Codex 实现 Track MVP 的交接文档。"
```

Track stores metadata and summary by default. It does not send file content to AI.

## Import Historical Material

```bash
track import file --path ./old-notes.md
track import folder --path ./docs --recursive
track import text --title "历史对话" --type chat_log --text "..."
```

Supported MVP file types:

- `.md`
- `.txt`
- `.json`
- `.py`

Imported material is stored as `source_materials` with `processed_status=pending`.

## Backfill Existing Projects

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

## Cost Guard

```bash
track cost
track cost status
track cost mode local_only
track cost mode strict_budget
track cost estimate "token 消耗"
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

AI commands are intentionally not enabled in the MVP. Future AI commands must use names like:

```bash
track ai-summarize artifact_001 --confirm-cost
track ai-extract source_001 --confirm-cost
```

Non-`ai-*` commands are local only.

## Test

```bash
python3 -m unittest discover -s tests -q
```

## MVP Limits

- No cloud sync.
- No multi-user collaboration.
- No web UI.
- No automatic ChatGPT history reading.
- No vector search.
- No default AI summarization.
- No automatic full-text AI analysis.

## Roadmap

- Optional `ai-*` commands with explicit confirmation.
- Local vector search.
- Web UI.
- Graph visualization.
- Timeline generation.
- Conflict detection.
