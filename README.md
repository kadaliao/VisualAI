# visual-prompt-cookbook

给 Codex 安装一个视觉提示词 skill，用来浏览视觉风格、补全变量，并生成可直接用于图片模型的提示词。

## 一行安装

不需要 clone 这个仓库，直接运行：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install-skill
```

安装后，skill 会位于：

```text
~/.codex/skills/visual-prompt-cookbook
```

重启 Codex 后就可以直接让 Codex 使用这个 skill。你可以说：

```text
帮我做一张适合小红书封面的视觉提示词
```

或者：

```text
打开 visual-prompt-cookbook 的风格 dashboard，我想先挑一个风格
```

## 更新

重新运行同一条命令即可覆盖安装到最新版：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install-skill
```

## 这个 Skill 做什么

- 从 `AI-Visual-Prompt-Cookbook` 整理出一批视觉风格。
- 提供本地 dashboard，方便浏览、筛选和选择风格。
- 让 Codex 根据你要做的图片主动补全风格变量。
- 默认输出完整提示词；只有你明确要求生成图片时，Codex 才会继续调用图像生成能力。

## 开发者命令

本仓库是 `visual-prompt-cookbook` skill 的源码和同步工具。Python 命令统一使用 `uv run python`。

从本地 checkout 安装：

```bash
uv run visualai-install-skill \
  --source-root skills/visual-prompt-cookbook \
  --skills-root ~/.codex/skills
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
