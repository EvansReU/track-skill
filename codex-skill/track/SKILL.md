---
name: track
description: MUST USE when the user says or invokes "Track", "Track ...", "track", "track this", "track save", "track 查 ...", "track pack", "track file", "track backfill", asks to record/recall project memory with Track, or wants to use the local Track project memory tool. Also use in an already tracked project when a turn contains important project decisions, questions, requirements, artifacts, tasks, blockers, or "remember/save/from now on" signals. This skill means call the local Track CLI; do not rebuild Track, do not interpret "track" as git tracking, and do not answer with generic tracking advice.
---

# Track

Use the local `track` CLI to record, recall, and package project memory. The CLI should be installed in PATH as `track`.

## Critical Behavior

- Treat `track` as Evans's local project-memory command, not as a request to build a new tool.
- Do not interpret `track` as git file tracking.
- Prefer running the CLI over explaining it.
- Track is local-first and default 0 token; do not call external AI for Track commands.
- Rule extraction auto-saves by default. Do not ask for confirmation before saving locally extracted Track records.
- For backfill/import on an existing large project, do not scan or read the whole project with Codex. Use `track import ...` and `track backfill extract`, which are local CLI operations.
- If deeper Codex/AI analysis would read many project files, summarize whole folders, inspect source code broadly, or build a semantic graph beyond local Track rules, ask the user for explicit confirmation first and state that Codex token usage may be high.
- In an already tracked project with auto Track enabled, automatically run `track auto --text "<short turn summary>"` at the end of important turns. The text must be only the current turn's short factual summary or relevant user quote, preferably under 300 Chinese characters; do not read history or files for this.
- Auto Track trigger signals include: 是否, 怎么, 如何, 为什么, 要不要, 能不能, 决定, 不做, 改成, 先做, 放弃, 默认, 必须, 生成, 文档, 代码, 方案, 交接, 待办, 下一步, 问题, 不符合预期, 偏离初衷, 修正, 重构, 保存, 记住, 以后, 从现在开始.
- Do not auto Track ordinary greetings, simple confirmations, non-project chat, repeated explanations, temporary examples, or follow-up questions with no new information.
- If this turn automatically records the current conversation or discussion with Track, end the user-facing reply with the exact marker `〖已Track〗`.

## Command Mapping

When the user says exactly `Track` or `track`, run `track Track`. The CLI maps this to the current workspace folder name. If the project is new, this creates the Track record, enables auto Track, and performs lightweight local backfill. If the project already exists, this is a manual force-save request for the current turn; run `track this --text "<short current turn summary>"` when there is current turn content to save.

When the user says `Track <query>`, run:

```bash
track Track "<query>"
```

This is a query only. Do not save the current turn and do not backfill.

When the user says `track this`, capture the current relevant conversation or user-provided text into a concise factual note, then run:

```bash
track this --text "<current discussion summary>"
```

If there is no usable current discussion text, ask the user for the text to save.

When the user says `track 查 <query>`, run:

```bash
track 查 "<query>"
```

When the user says `track pack`, run:

```bash
track pack
```

When the user says `track save`, run:

```bash
track save
```

This is mostly compatibility; `track this` already auto-saves.

## File And Backfill

For `track file`, pass through file path or metadata:

```bash
track file --path <path>
```

For existing project history:

```bash
track backfill
track import file --path <path>
track import folder --path <path> --recursive
track backfill extract
track backfill review
track backfill complete
```

These commands are the default path for old projects. They may read files locally through the Track CLI, but Codex should not open and analyze the full file contents unless the user explicitly confirms a higher-token Codex analysis pass.

## Reporting Back

After running a Track command, summarize the useful result briefly:

- project entered or created
- records auto-saved
- recall highlights
- pack location/output
- any error and the exact next fix

Do not paste huge raw JSON unless the user asks.

If the command auto-saved current conversation content, the final line of the reply must be:

```text
〖已Track〗
```

## Fallback

If `track` is not found in PATH, run it from the local repository:

```bash
cd /Users/evans/Documents/history-track && python3 -m track.cli <args>
```
