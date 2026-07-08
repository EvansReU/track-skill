---
name: track
description: MUST USE when the user says or invokes "track", "track this", "track save", "track 查 ...", "track pack", "track file", "track backfill", asks to record/recall project memory with Track, or wants to use the local Track project memory tool. This skill means call the local Track CLI; do not rebuild Track, do not interpret "track" as git tracking, and do not answer with generic tracking advice.
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

## Command Mapping

When the user says exactly `track`, run `track <project-name>`, using the current workspace folder name as the project name.

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

## Fallback

If `track` is not found in PATH, run it from the local repository:

```bash
cd /Users/evans/Documents/history-track && python3 -m track.cli <args>
```
