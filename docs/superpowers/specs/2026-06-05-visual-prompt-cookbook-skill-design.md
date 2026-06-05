# Visual Prompt Cookbook Skill 设计

日期：2026-06-05

## 背景

`kadaliao/AI-Visual-Prompt-Cookbook` 提供了一组优秀的视觉提示词风格模板。当前上游仓库的核心资产是 `styles/<slug>/style.json`、两张预览图、`docs/CATALOG.md` 和 `schemas/style-v2.1.schema.json`。每个 `style.json` 包含风格摘要、变量声明、风格锚点、避开源内容、负向提示词、示例变量值和 `prompt_template`。

这些模板已经结构化，但普通使用者仍需要自己浏览风格、理解变量、填完整模板。VisualAI 的第一版目标是把它变成 Codex 可调用的个人 skill：用户说“想做精致图片”时，可以打开一个本地 dashboard 看风格，选中风格后由 Codex 主动补全变量，默认输出最终可用提示词；只有用户明确要求时才生成图片。

## 已确认决策

- `VisualAI` 是源码仓库，同时同步安装一份可用 skill 到 `~/.codex/skills/visual-prompt-cookbook`。
- Cookbook 上游是可刷新数据源，不做一次性拷贝；本地记录 upstream URL、commit 和同步时间。
- 第一版采用“混合工作台”：dashboard 负责可视化风格库和变量草稿，对话负责理解需求、主动补变量和输出最终 prompt。
- Dashboard 职责范围是“风格 + 变量草稿”，不是完整 Prompt Studio。
- AI 默认主动补全变量；缺失信息用合理推断补齐，并标注哪些值是推断得到的。
- 默认输出最终 prompt；当用户明确说“生成图片”时，再调用现有 `imagegen` 能力。
- Python 操作遵守本仓库约束，统一使用 `uv run python`、`uv pip install`、`uv venv`。
- Commit message 不添加 `Co-Authored-By: Codex`。

## 目标

1. 用户能通过 skill 快速发现 Cookbook 风格，看到预览图、编号、名称、摘要和关键标签。
2. 用户能通过点击 dashboard 或在对话中输入编号/名称选择风格。
3. Codex 能读取选中风格的 `style.json`，根据用户一句自然语言需求主动生成完整变量草稿。
4. Codex 能把 `prompt_template`、变量值、风格锚点和避开源内容组合成最终 prompt。
5. 用户明确要求图片时，Codex 将最终 prompt 交给现有图像生成流程。
6. 本地资产能随 upstream 更新并重建索引。

## 非目标

- 不做后台常驻服务。
- 不做云端部署、多用户账号或同步。
- 不做浏览器端项目历史保存。
- 不做完整变量表单编辑器或实时 prompt studio。
- 不做多模型路由或模型参数控制。
- 不做自动定时同步 upstream；第一版提供手动同步脚本。

## 用户流程

1. 用户说“我想做一张精致图片”“做一个高级海报”“用这个风格生成提示词”等。
2. `visual-prompt-cookbook` skill 触发。
3. 如果用户还没有指定风格，Codex 启动 dashboard，本地 serve 风格库页面。
4. Dashboard 展示全部风格：编号、名称、摘要、预览图、分类/标签、搜索入口和推荐候选。
5. 用户点击风格，或在对话中告知编号、slug、名称。
6. Codex 读取风格详情，结合用户意图主动补全变量。
7. Codex 输出：
   - 选中风格名称和编号。
   - 变量草稿，其中明确标注用户提供值和 AI 推断值。
   - 最终 prompt。
   - 如果用户想生成图片，提示将使用该 prompt 进入图像生成。
8. 用户要求改变量时，Codex 更新变量并重新渲染 prompt。

## 架构

系统由四块组成：

- **源码仓库**：`/Users/liaoxingyi/Documents/VisualAI`，保存 skill 源码、dashboard、同步脚本、测试和设计文档。
- **安装版 skill**：`~/.codex/skills/visual-prompt-cookbook`，由源码仓库同步生成，供 Codex 会话自动发现。
- **Cookbook 资产缓存**：保存从 upstream 同步来的 `style.json`、预览图、schema、LICENSE 和元信息。
- **Dashboard 服务**：本地静态页面 + Python HTTP 服务，用于风格浏览和选择事件记录。

Dashboard 不替代对话。它只负责让用户看见和选择风格，并展示当前变量草稿；对话仍负责理解需求、变量补全、prompt 渲染和图片生成转交。

## 建议文件结构

```text
VisualAI/
  .gitignore
  pyproject.toml
  README.md
  docs/
    superpowers/
      specs/
        2026-06-05-visual-prompt-cookbook-skill-design.md
  skills/
    visual-prompt-cookbook/
      SKILL.md
      agents/
        openai.yaml
      references/
        usage-workflow.md
      scripts/
        sync_cookbook.py
        build_index.py
        serve_dashboard.py
        render_prompt.py
        install_skill.py
      assets/
        dashboard/
          index.html
          app.js
          styles.css
        cookbook/
          upstream.json
          manifest.json
          LICENSE
          schema/
            style-v2.1.schema.json
          styles-index.json
          styles/<slug>/
            style.json
            preview-16x9.jpg
            preview-9x16.jpg
  tests/
```

第一版可合并 `sync_cookbook.py` 和 `build_index.py`，但接口上要保持“同步 upstream”和“重建索引”两个概念清晰。

## Skill 行为

`SKILL.md` 保持短而清晰，负责触发和流程导航：

- 当用户想制作高质量图片、海报、广告图、封面、社交媒体视觉、视觉提示词，或明确提到 Cookbook 风格时触发。
- 如果用户未指定风格，先运行 dashboard 服务，告诉用户本地 URL，并说明可以点击或回复编号。
- 如果用户指定风格，直接读取对应 `style.json`。
- 根据 `environment_variables` 生成完整变量草稿。
- 对用户未明确给出的变量进行推断，并在回复中标记。
- 使用 `render_prompt.py` 或等价逻辑渲染最终 prompt。
- 默认只输出 prompt；只有用户明确要求生成图片时才调用图像生成能力。

为了节省上下文，skill 不应把所有风格数据写进 `SKILL.md`。详细风格数据保存在 `assets/cookbook/`，需要时由脚本查询或读取单个风格 JSON。

## Cookbook 同步

同步脚本职责：

1. 接收 upstream URL，默认 `git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git`。
2. 拉取或更新临时/缓存 checkout。
3. 复制必要文件：
   - `styles/*/style.json`
   - `styles/*/preview-16x9.jpg`
   - `styles/*/preview-9x16.jpg`
   - `schemas/style-v2.1.schema.json`
   - `LICENSE`
4. 生成 `upstream.json`：
   - upstream URL
   - commit SHA
   - synced_at
   - style_count
   - schema version/path
   - license identifier or source
5. 生成 `styles-index.json`，供 dashboard 和查询脚本使用。

由于 upstream 是 MIT License，同步后的 skill 资产必须保留 upstream `LICENSE`。Dashboard 或 README 中应包含来源说明。

## 风格索引

`styles-index.json` 至少包含：

- `id`：稳定编号，从 1 开始，按同步后的确定性排序生成。
- `style_name`
- `style_slug`
- `style_summary`
- `preview_16x9`
- `preview_9x16`
- `environment_variables` 名称列表
- `tags`：由摘要、目录类别或启发式规则生成。
- `updated_from_commit`

编号需要在同一份索引内稳定。Upstream 新增风格时，可以追加或按 slug 排序重排；如果重排，需要 dashboard 显示 slug，避免用户只依赖编号。

## Dashboard 设计

第一版 dashboard 是静态前端，由 Python 本地 HTTP 服务承载：

- 首页展示风格总数、upstream commit、同步时间。
- 提供搜索框，支持按名称、slug、摘要、标签搜索。
- 风格卡片展示 16:9 预览图、名称、编号、摘要和标签。
- 点击风格后显示详情：两张预览图、变量名、变量说明、示例值和选择按钮。
- 选择事件写入本地事件文件，Codex 读取后继续对话。
- 变量草稿可以作为详情面板的一部分显示，但不要求浏览器端编辑后回写。

页面不需要构建工具，避免第一版引入前端依赖。若后续需要更复杂交互，再升级为小型前端应用。

## 变量补全与 Prompt 渲染

变量补全以 `style.json.environment_variables` 为契约。第一版流程：

1. 读取变量说明和示例值。
2. 从用户需求中抽取明确值，例如主体、场景、文案、比例、品牌/产品、用途。
3. 对缺失项生成合理推断值。
4. 生成变量草稿：
   - `value`
   - `source`: `user` 或 `inferred`
   - `reason`：简短说明为什么这样填。
5. 将变量插入 `prompt_template`。
6. 将 `style_fidelity_anchors` 和 `source_content_to_avoid` 以模板约定方式加入变量或保持模板原有表达。
7. 返回最终 prompt 和变量草稿。

渲染脚本应对缺失变量报错，而不是悄悄留 `{VARIABLE}` 占位符。输出前要检查最终 prompt 中没有未替换占位符。

## 安装与更新

提供 `install_skill.py`：

- 将 `skills/visual-prompt-cookbook` 同步到 `~/.codex/skills/visual-prompt-cookbook`。
- 安装前可以备份已有同名 skill，或输出覆盖提示；第一版在本地开发场景下可直接覆盖。
- 安装后验证 `SKILL.md`、`agents/openai.yaml`、脚本和 assets 存在。

更新流程：

```bash
uv run python skills/visual-prompt-cookbook/scripts/sync_cookbook.py
uv run python skills/visual-prompt-cookbook/scripts/install_skill.py
```

## 测试与验证

自动化验证：

- `styles-index.json` 可解析，风格数量与实际 `style.json` 数量一致。
- 每个索引项对应的 `style.json` 和预览图存在。
- 抽样至少 3 个风格，使用示例或测试变量渲染 prompt，确认无残留 `{VARIABLE}`。
- 缺失变量时 `render_prompt.py` 返回清晰错误。
- `SKILL.md` frontmatter 合法，`agents/openai.yaml` 与 skill 描述一致。

可视化验证：

- 用 dashboard 本地服务打开页面。
- 确认风格总数、预览图、详情页和选择事件工作。
- 至少用一个真实需求走完整链路：选风格、补变量、输出 prompt。

## 验收标准

第一版完成时，应满足：

- 在当前源码仓库中可以运行同步脚本，生成 Cookbook 资产缓存和索引。
- 可以安装到 `~/.codex/skills/visual-prompt-cookbook`。
- 新会话中用户说想做精致图片时，skill 能指导打开 dashboard。
- 用户选择风格或告知编号后，Codex 能主动补全变量并输出最终 prompt。
- 用户明确要求生成图片时，Codex 能把该 prompt 交给图像生成能力。
- README 或 skill 中注明 Cookbook 来源和 MIT License 保留策略。

## 风险与处理

- **Upstream schema 变化**：同步时记录 schema 路径和 commit；索引生成失败时输出具体 style slug 和字段。
- **编号不稳定**：dashboard 同时显示编号和 slug；对话接受 slug/名称作为更稳定引用。
- **上下文膨胀**：默认只读取索引和单个 `style.json`，不把完整风格库塞入对话。
- **用户需求过少**：按已确认策略主动补全，并标注推断项，让用户能快速修改。
- **图片生成边界混乱**：默认只输出 prompt；只有明确要求生成图才调用 imagegen。
- **许可证遗漏**：同步 `LICENSE`，并在元信息和文档中保留 upstream attribution。
