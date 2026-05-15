# xwysyy-typst — AGENTS.md

> AGENTS.md 是给 AI assistant 的导航地图，不是百科。
> 本项目规模小，多数 dev-templates 的标准文档都不存在（见末尾"本项目不存在的文档"）。

---

## 项目本质

- 单仓个人 typst slide 模板 + 笔记模板 + 示例（sky / sunset 两套 slide 主题 + 主题无关的笔记模式）
- 单人维护，无 CI/CD、无 contributor
- 主题文件 `xwysyy.typ` 派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)（MIT），整体改名为 `xwysyy-*` 前缀

## 必读

暂无。本项目尚无 `docs/project-memo.md`（跨任务铁律 / 偏好沉淀）；当跨会话信号 >=2 条同类时再按 `~/.claude/rules/dev-protocols.md § Project Memo Protocol` 升级创建。

## 关键文件

| 文件 | 作用 |
|------|------|
| `xwysyy.typ` | 单文件主题：themes 字典、show 规则、page 配置、slide 组件（`textbox`、`info`、`outline-slide`、`end-slide`、`focus-slide`、`image-slide`）、笔记入口（`xwysyy-note`）、颜色宏（`red`/`bred`/`yellow`/`byellow`）。`outline-slide` 自动过滤 `<touying:hidden>` 标签且 >5 章自动两列。`frozen-counters` 默认冻结 `figure` 和 `math.equation` 计数器 |
| `xwysyy-extras.typ` | 可选扩展：cetz/fletcher 的 `touying-reducer` 包装（绘图+`#pause` 动画）+ theorion 定理环境一站式导出 |
| `examples/slides-sky.typ` | sky 主题演示 deck |
| `examples/slides-sunset.typ` | sunset 主题演示 deck |
| `examples/note.typ` | 笔记模式演示（主题无关） |
| `examples/refs.bib` | 笔记演示用 BibTeX |
| `examples/xwysyy.typ` | 符号链接 -> `../xwysyy.typ` |
| `examples/xwysyy-extras.typ` | 符号链接 -> `../xwysyy-extras.typ` |
| `typst.toml` | 包清单：name/version/entrypoint，发版时同步 CHANGELOG |
| `CHANGELOG.md` | 版本变更记录，遵循 Keep a Changelog 格式 |
| `README.md` | 用户视角文档：用法、组件参考、主题系统、兼容性 |
| `docs/USAGE.md` | 完整 API 参考：所有 slide 版式、组件、非 slide 文档入口 |
| `docs/CUSTOMIZATION.md` | 自定义指南 + 配合 touying 0.7.x 高级特性 |
| `LICENSE` | MIT，沿用上游 |

## 工作规则（项目层面）

完整开发纪律见 `~/.claude/rules/dev-principles.md` + `dev-protocols.md`；以下是本项目特有提醒。

- **改完必编译**：任何对 `xwysyy.typ` 或示例的修改完成后，跑 `typst compile examples/slides-sky.typ && typst compile examples/slides-sunset.typ && typst compile --root . examples/note.typ` 验证 slide 两个主题 + 笔记都无错误才算完成。
- **文档同步 SOP**：按改动类型查表同步文档，不再维护行号引用。

  | 改了什么 | 必须同步 |
  |---------|---------|
  | 新增/删除/改名公开函数 | README 组件速查 + USAGE 版式/组件章节 + AGENTS 关键文件表 |
  | 改主题色字段 | README 主题配色表 + CUSTOMIZATION §1 + THEME-GENERATOR |
  | 改 show rule 行为 | USAGE §6 show 规则速览 |
  | 改 example deck 结构 | 重新生成 preview PNG + README 预览表 |
  | 纯内部重构（不改公开 API） | 无 |
  | 发版 | CHANGELOG.md + typst.toml version + git tag |
- **主题色变量是契约**：`themes` 字典中每套主题的 `sea` / `sky` / `skyl` / `skyll` / `paper` 以及 `header-fill` / `header-text` / `page-fill` 既是颜色定义，也通过 `config-colors` 映射到 touying 的语义槽（`neutral-dark = sea` 等）。改名要同步改 `xwysyy-pre` 内 `config-colors(...)` 调用，否则下游 slide 组件会拿到错误颜色。运行时通过 `_theme-state`（state）向 `textbox` 等组件传播主题色。
- **函数命名前缀**：当前所有公开主题函数前缀为 `xwysyy-`（`xwysyy-pre`、`xwysyy-slide`、`xwysyy-elements`、`xwysyy-note`）。新增函数沿用此前缀；`title-slide` / `outline-slide` / `textbox` / `end-slide` 等通用 helper 不带前缀。
- **笔记模式是主题无关的**：`xwysyy-note` 不使用 `themes` 字典或 `_theme-state`，所有颜色为灰度 + 固定蓝色链接。改笔记样式不需要关心 slide 主题系统。
- **typst + touying 边界 bug**：`config-info(author: [])`（空 content）在 typst 0.14 + touying 0.7.3 组合下仍会触发 touying `markup-text` 把空 content 处理成 none，失败于内部类型检查（`@preview/touying:0.7.3/src/slides.typ:37`）。空作者用 `author: " "` 绕开，不要回退到 `[]`。
- **不要随便引入 typst package**：核心依赖只有 `@preview/touying:0.7.3` 与 `@preview/physica:0.9.5`。`xwysyy-extras.typ` 额外依赖 `cetz`/`fletcher`/`theorion`，但它是可选文件不影响核心模板。新增核心依赖前先评估是否可在 `xwysyy.typ` 内手写实现。
- **inline code 与 block code 分开处理**：`xwysyy-elements` 中 `raw.where(block: true)` 用 `block(width: 100%)` 全宽显示，`raw.where(block: false)` 用 `box(baseline: 0.2em)` 内联显示。修改代码样式时需同步改两处。
- **箭头 show rule 用 math 模式**：箭头替换（`->` -> `$->$` 等）必须用 `$...$` 进入 math 模式才能渲染为箭头符号。不要用 `math.limits(it)`（只管上下标位置，不做符号转换）。长箭头（`-->`、`==>`）的 show rule 必须定义在短箭头（`->`、`=>`）之前，否则短规则会先截取。

## 改主题的常见动线

- **改色 / 新增主题**：编辑 `xwysyy.typ` 顶部 `themes` 字典，新增一个 key 即可。每个主题需包含 `sea`/`sky`/`skyl`/`skyll`/`paper`/`header-fill`/`header-text`/`page-fill` 共 8 个字段。
- **改字号**：`xwysyy-pre` 中 `set text(... size: 5.5mm)`；或示例 deck 顶部 `#set text(size: ...)` 临时覆盖。
- **改 slide 顶部 / 底部装饰**：编辑 `xwysyy-slide` 内的 `header(self)` / `footer(self)` 函数。header 使用 `block` 固定高度 2.5em，颜色来自 `config-store` 的 `header-fill`/`header-text`。footer 简化为可选文字 + 页码（无背景/边框）。
- **新增页面版式**：仿照 `focus-slide` / `end-slide` 写一个 `touying-slide-wrapper` 即可。**必须用 `utils.merge-dicts(self, config-page(...))`，不要用 `show: touying-slides.with(...)`**——后者在 touying 0.7.x 会产生 ghost slide（参见 `title-slide` 实现）。
- **改 slide show 规则**：编辑 `xwysyy-elements` 内的 show 规则块（仅影响 slide 模式）。注意 raw 有 block: true 和 block: false 两条 show rule。
- **改笔记 show 规则**：编辑 `xwysyy-note` 函数内的对应规则（独立于 slide，不共享 `xwysyy-elements`）。
- **`textbox` 组件**：浅色圆角文本框，背景色为当前主题的 `skyll`。单列直接全宽 block；多列模式内部用 `components.lazy-layout` + `components.lazy-v(1fr)` 实现等高。颜色通过 `_theme-state` 读取。

## 本项目不存在的文档（防止 AI 强行创建）

- 没有 `docs/spec.md` — 模板没有"功能需求"，无外部契约
- 没有 `docs/implementation-plan.md` — 没有多步开发任务
- 没有 `docs/feature-flow.md` — 模板就是一组 show 规则集合
- 没有 `docs/architecture.md` — 单文件单模块
- 没有 `docs/iteration-notes.md` — 单人维护，`git log` 即历史

> `docs/USAGE.md` 和 `docs/CUSTOMIZATION.md` 已存在（见上方"关键文件"表），是用户文档，不在此清单。

## 上游 / 致谢

主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)（MIT），底层基于 [touying](https://github.com/touying-typ/touying)。
