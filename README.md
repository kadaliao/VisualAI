# VisualAI

这个仓库维护一个本地 Codex skill：`visual-prompt-cookbook`。

第一版目标：

- 从 `kadaliao/AI-Visual-Prompt-Cookbook` 同步风格 JSON 和预览图。
- Serve 本地 dashboard，帮助用户浏览和选择风格。
- 让 Codex 主动补全变量，并默认输出最终可用提示词。
- 用户明确要求生成图片时，再把提示词交给图像生成能力。

Python 命令统一使用 `uv run python`。

## 常用命令

同步上游 Cookbook：

```bash
uv run python skills/visual-prompt-cookbook/scripts/sync_cookbook.py
```

启动风格 dashboard：

```bash
uv run python skills/visual-prompt-cookbook/scripts/serve_dashboard.py
```

安装到本机 Codex skills：

```bash
uv run python skills/visual-prompt-cookbook/scripts/install_skill.py
```

## 来源与许可证

风格数据来自 `git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git`。同步脚本会保留上游 `LICENSE`、schema、commit 和同步时间；当前同步资产位于 `skills/visual-prompt-cookbook/assets/cookbook/`。
