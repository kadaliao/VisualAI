# visual-prompt-cookbook

一个给 AI agent 用的视觉提示词 skill：选择视觉风格，补全变量，生成可直接用于图片模型的 prompt。

## 安装

不需要 clone 这个仓库，运行一条命令，然后在交互菜单里选择你的 agent：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install
```

支持 Codex、Claude Code、Cursor、Gemini CLI、OpenCode、Windsurf、OpenClaw、Hermes Agent，也可以选择安装到全部内置目标或自定义目录。

脚本化安装可以跳过菜单：

```bash
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent codex
uvx --from git+https://github.com/kadaliao/VisualAI.git visualai-install --agent all
```

## 使用

安装后重启对应 agent，然后直接说：

```text
帮我做一张适合小红书封面的视觉提示词
```

需要看风格库时说：

```text
打开 visual-prompt-cookbook 的风格 dashboard
```

更新到最新版时，重新运行安装命令即可。
