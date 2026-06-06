# visual-prompt-cookbook

给 AI agent 安装一个视觉提示词 skill，用来浏览视觉风格、补全变量，并生成可直接用于图片模型的提示词。

## 一行安装

不需要 clone 这个仓库，直接运行：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install
```

安装器会让你选择常用 agent，并把 skill 安装到对应位置。

## 直接指定 Agent

也可以跳过交互，直接传入目标 agent：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent codex
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent claude
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent cursor
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent gemini
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent hermes
```

查看完整列表：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --list-agents
```

当前支持：

| Agent | 默认安装位置 |
| --- | --- |
| Codex | `~/.codex/skills/visual-prompt-cookbook` |
| Claude Code | `~/.claude/skills/visual-prompt-cookbook` |
| Cursor | `~/.cursor/skills/visual-prompt-cookbook` |
| Gemini CLI | `~/.gemini/extensions/visual-prompt-cookbook` |
| OpenCode | `~/.config/opencode/skills/visual-prompt-cookbook` |
| Windsurf | `~/.codeium/windsurf/skills/visual-prompt-cookbook` |
| OpenClaw | `~/.openclaw-autoclaw/skills/visual-prompt-cookbook` |
| Hermes Agent | `~/.hermes/skills/visual-prompt-cookbook` |

安装到所有内置目标：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent all
```

安装到自定义目录：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install \
  --agent custom \
  --target-root ~/.agents/skills
```

## 使用

安装后，重启对应 agent，让它重新加载本地 skill。之后可以直接说：

```text
帮我做一张适合小红书封面的视觉提示词
```

或者：

```text
打开 visual-prompt-cookbook 的风格 dashboard，我想先挑一个风格
```

## 更新

重新运行同一条安装命令即可覆盖安装到最新版。

## 这个 Skill 做什么

- 从 `AI-Visual-Prompt-Cookbook` 整理出一批视觉风格。
- 提供本地 dashboard，方便浏览、筛选和选择风格。
- 让 agent 根据你要做的图片主动补全风格变量。
- 默认输出完整提示词；只有你明确要求生成图片时，agent 才会继续调用图像生成能力。

## 开发者命令

本仓库是 `visual-prompt-cookbook` skill 的源码和同步工具。Python 命令统一使用 `uv run python`。

从本地 checkout 安装：

```bash
uv run visualai-install \
  --agent codex \
  --source-root skills/visual-prompt-cookbook
```

同步上游 Cookbook：

```bash
uv run python skills/visual-prompt-cookbook/scripts/sync_cookbook.py
```

启动风格 dashboard：

```bash
uv run python skills/visual-prompt-cookbook/scripts/serve_dashboard.py
```

## 来源与许可证

风格数据来自 `git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git`。同步脚本会保留上游 `LICENSE`、schema、commit 和同步时间；当前同步资产位于 `skills/visual-prompt-cookbook/assets/cookbook/`。
