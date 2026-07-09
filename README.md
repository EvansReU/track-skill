# Track

语言 / Language: [中文](#中文) | [English](#english)

## 中文

Track 是给长期 AI 项目用的“项目记忆追踪器”。

它解决的不是“让 AI 更聪明”，而是让你在一个复杂项目里，过了几天、换了线程、忘了来龙去脉时，能低成本找回：

- 当时问过什么问题
- 后来做了什么决策
- 为什么放弃某个方案
- 某个文档/代码/方案是怎么来的
- 现在仍然有效的约束和待办是什么

Track 的默认原则是：**本地记录，低成本召回，不让项目记忆系统变成 token 黑洞。**

### 你只需要记住两个用法

#### `Track`

第一次在项目里使用：

- 为当前项目建档
- 做一次轻量本地补录
- 开启后续自动 Track

已经建档后再次使用：

- 强制保存当前轮讨论

#### `Track 关键词`

查询当前项目中和关键词有关的历史记录。

例如：

```text
Track token消耗
Track 自动记录
Track 交接文档
```

Track 会返回相关问题、决策、上下文、产出物和关系线索。

### 自动 Track

项目建档后，Codex 在重要轮次结束时可以自动调用 Track 保存本轮短摘要。

会自动记录的内容包括：

- 新问题
- 新决策
- 需求变化
- 目标调整
- 重要结论
- 产出物
- 待办事项
- 阻塞点
- 用户明确说“保存 / 记住 / 以后 / 从现在开始”

自动 Track 默认只保存本轮极短摘要或用户原话片段，不读取历史，不扫描项目，不调用 AI。

自动记录成功后，Codex 回复末尾应显示：

```text
〖已Track〗
```

暂停或恢复自动 Track：

```text
Track off
Track on
```

### 追溯：让你恢复当时的现场

普通搜索只能告诉你“搜到了什么”。Track 更重要的是帮你恢复记忆。

使用：

```text
Track why token消耗
Track 追溯 交接文档
```

你会得到一个“回忆包”，包括：

- 一句话帮你想起来
- 当时的背景问题
- 关键决策
- 相关上下文
- 相关产出物
- 当前状态
- 可追溯关系线索
- 你可以继续追问什么

示例输出形态：

```text
你问的是：为什么 Track 要默认 0 token？

一句话帮你想起来：
当时做这个决策，是因为你担心项目记忆工具本身变成持续消耗 token 的黑洞。

关键决策：
- Track 默认本地运行，不调用云端 AI。
- 非 ai-* 命令不得调用 AI。
- Backfill 时 Codex 不得自行扫描整个项目，除非用户确认。

当前状态：
- 这个约束仍然有效。
- 深度整理只能在用户确认后进行。
```

### Track 和直接问 Codex 的区别

直接问 Codex，适合当前上下文里的思考。

Track 适合跨线程、跨时间找回历史。

没有 Track 时，Codex 可能需要重新读大量文件或聊天记录，也可能只能靠猜。  
有 Track 时，Codex 先拿到一个小型、结构化、可审计的回忆包，再帮你继续判断和推进。

简单说：

```text
Track 找回事实和关联。
Codex 负责解释、判断和继续推进。
```

### 一次典型工作流

```text
Track
```

先给项目建档。

之后正常和 Codex 讨论项目。重要轮次会自动 Track。

想回忆某件事时：

```text
Track token消耗
```

想追溯来龙去脉时：

```text
Track why token消耗
```

想开新线程继续项目时：

```text
track pack
```

### 安装

```bash
python3 -m pip install -e .
track init
```

### 在 Codex 中启用 Skill

如果希望在 Codex 里直接输入 `Track` 就调用本工具，请安装仓库里的 Codex Skill：

```bash
mkdir -p ~/.codex/skills
cp -R codex-skill/track ~/.codex/skills/track
```

然后开启新的 Codex 线程或重启 Codex，让 Skill 列表重新加载。

### 默认不做什么

Track 默认不做这些事：

- 不调用云端 AI
- 不做 embedding
- 不扫描整个项目让 Codex 深度分析
- 不全文召回
- 不把历史材料默认塞进 AI 上下文

如果你需要“深度整理整个项目历史”，Track/Codex 必须先征求确认，并说明这会消耗较多 Codex token。

### 常用命令

```bash
track              # 当前项目建档或进入
track Track xxx    # 查询 xxx
track why xxx      # 生成回忆包
track auto --text "本轮短摘要"
track pack         # 生成项目上下文包
track off          # 暂停自动 Track
track on           # 恢复自动 Track
```

### 测试

```bash
python3 -m unittest discover -s tests -q
```

## English

Track is a local-first project memory tracker for long-running AI-assisted projects.

It is not meant to make AI magically smarter. It gives you a low-cost way to recover the history of a complex project when you have changed threads, lost context, or forgotten why something was decided.

Track helps you recall:

- previous questions
- key decisions
- abandoned options
- why an artifact exists
- current constraints and tasks
- related historical context

Its default promise is: **local memory, low-cost recall, no token black hole.**

### Two Core Uses

#### `Track`

First use in a project:

- creates the project memory record
- runs lightweight local backfill
- enables auto Track

In an already tracked project:

- force-saves the current turn

#### `Track keyword`

Searches the current project for historical records related to `keyword`.

Examples:

```text
Track token cost
Track auto tracking
Track handoff document
```

### Auto Track

After a project is tracked, Codex may automatically save important turns through Track.

Auto Track is for:

- new questions
- decisions
- requirement changes
- goal changes
- important conclusions
- artifacts
- tasks
- blockers
- explicit “remember/save/from now on” signals

Auto Track only passes a short current-turn summary or user quote. It does not read history, scan files, or call AI.

When it saves successfully, Codex should end with:

```text
〖已Track〗
```

Pause or resume auto Track:

```text
Track off
Track on
```

### Trace Memory

Use:

```text
Track why token cost
Track 追溯 handoff document
```

Track returns a memory brief, not just search results:

- what you asked about
- one-line memory cue
- original background
- key decisions
- related context
- related artifacts
- current status
- relationship trail
- useful follow-up prompts

### Track vs Asking Codex Directly

Ask Codex directly for reasoning in the current context.

Use Track when the relevant context may live in another thread, another day, or another artifact.

Track finds the facts and relationships. Codex interprets them and helps you move forward.

### Install

```bash
python3 -m pip install -e .
track init
```

### Enable The Codex Skill

```bash
mkdir -p ~/.codex/skills
cp -R codex-skill/track ~/.codex/skills/track
```

Then start a new Codex thread or restart Codex.

### Defaults

Track does not:

- call cloud AI
- create embeddings
- ask Codex to scan the whole project
- recall full text by default
- push historical material into AI context by default

Deep project-history analysis requires explicit user confirmation because it may consume many Codex tokens.

### Common Commands

```bash
track
track Track keyword
track why keyword
track auto --text "short current-turn summary"
track pack
track off
track on
```

### Test

```bash
python3 -m unittest discover -s tests -q
```
