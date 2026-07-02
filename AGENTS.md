# xwysyy-typst — AGENTS.md

> AGENTS.md 是给 AI assistant 的导航地图，不是百科。
> 本项目规模小，多数 dev-templates 的标准文档都不存在（见末尾"本项目不存在的文档"）。

---

## 项目本质

- 单仓个人 typst slide 模板 + 笔记模板 + Universe template + 示例（6 套 slide 主题 + 主题无关的笔记模式 + `xwysyy-doc` 双产物模式）
- 单人维护，有 GitHub Actions 视觉回归，无 contributor
- 主题文件 `xwysyy.typ` 派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)（MIT），整体改名为 `xwysyy-*` 前缀

## 必读

暂无。本项目尚无 `docs/project-memo.md`（跨任务铁律 / 偏好沉淀）；当跨会话信号 >=2 条同类时再按 `~/.claude/rules/dev-protocols.md § Project Memo Protocol` 升级创建。

## 关键文件

| 文件 | 作用 |
|------|------|
| `xwysyy.typ` | facade entry，re-export `src/*.typ` 各子模块 + 包级 `physica` / `touying` import + `super-T-as-transpose` show 规则。用户写 `#import "xwysyy.typ": *` 一次拿全 |
| `xwysyy-extras.typ` | shim，re-export `src/extras.typ`（cetz / fletcher / theorion 集成） |
| `src/themes.typ` | `themes` 字典（sky / sunset / forest / midnight / violet / graphite）+ 主题字段校验 `_resolve-theme` + 顶层色变量（`sea` / `sky` / `skyl` / `skyll` / `paper`）+ `_theme-state` + 颜色宏（`red`/`bred`/`yellow`/`byellow`） |
| `src/elements.typ` | 共享 show-chain `xwysyy-elements`（slide 共用）+ `info` + `textbox` |
| `src/note.typ` | 笔记入口 `xwysyy-note`（A4，主题无关，show 规则独立） |
| `src/slides.typ` | slide 入口 `xwysyy-pre` + 双产物入口 `xwysyy-doc` + 7 种版式（`xwysyy-slide`、`title-slide`、`outline-slide`、`new-section-slide`、`focus-slide`、`image-slide`、`end-slide`）。`outline-slide` 自动过滤 `<touying:hidden>` 标签且 >5 章自动两列，`title: auto` 按 `text.lang` 输出 `Contents` / `目录`。`frozen-counters` 默认冻结 `figure` 和 `math.equation` 计数器 |
| `src/extras.typ` | `touying-reducer` 包装的 `cetz-canvas` / `fletcher-diagram` + theorion 全套环境导出 |
| `examples/slides-sky.typ` | sky 主题演示 deck |
| `examples/slides-sunset.typ` | sunset 主题演示 deck |
| `examples/note.typ` | 笔记模式演示（主题无关） |
| `examples/theme-preview.typ` | 可通过 `--input theme=<name>` 渲染任意内置主题的预览 deck |
| `examples/dual-source.typ` | `xwysyy-doc` 双产物示例；默认编译 deck，`--input mode=note` 编译 A4 讲义 |
| `examples/refs.bib` | 笔记演示用 BibTeX |
| `template/main.typ` | Universe template 脚手架入口，使用 `#import "@preview/xwysyy:0.3.0": *` |
| `thumbnail.png` | Universe template thumbnail，由 `template/main.typ` 首页渲染生成 |
| `typst.toml` | 包清单：name/version/entrypoint/template/exclude，发版时同步 CHANGELOG |
| `CHANGELOG.md` | 版本变更记录，遵循 Keep a Changelog 格式 |
| `README.md` | 用户视角文档：用法、组件参考、主题系统、兼容性 |
| `docs/USAGE.md` | 完整 API 参考：所有 slide 版式、组件、非 slide 文档入口 |
| `docs/CUSTOMIZATION.md` | 自定义指南 + 配合 touying 0.7.x 高级特性 |
| `docs/THEME-GENERATOR.md` | AI 生成主题字典提示词，默认指导用户直接传给 `theme` 参数 |
| `docs/DUAL-OUTPUT-DESIGN.md` | `xwysyy-doc` 入口形态、note 模式降级规则、pause 语义和共享组件设计 |
| `scripts/gen-previews` | 重新生成 README preview PNG，可带 `--with-baseline` 同步视觉基线 |
| `scripts/render-visuals` | 渲染视觉回归 PNG 集；内部传 `--input visual-ci=true` 以使用 CI 可安装字体 |
| `scripts/compare-png` | 无 ImageMagick 依赖的 PNG 像素比较器，可输出 diff PNG |
| `scripts/check-theme-contrast` | 解析 `src/themes.typ` 并检查主题对比度 |
| `.github/workflows/visual-regression.yml` | 编译示例、检查主题对比度、渲染视觉基线并比较 |
| `tests/fixtures/` | 自定义主题、目录标题、字体参数等编译验证 fixture |
| `tests/visual-baseline/` | CI 视觉回归基线 PNG |
| `LICENSE` | MIT，沿用上游 |

## 工作规则（项目层面）

完整开发纪律见 `~/.claude/rules/dev-principles.md` + `dev-protocols.md`；以下是本项目特有提醒。

- **改完必编译**：任何对 `xwysyy.typ` / `src/*.typ` / 示例 / 模板脚手架的修改完成后，至少跑 `typst compile --root . examples/slides-sky.typ && typst compile --root . examples/slides-sunset.typ && typst compile --root . examples/note.typ && typst compile --root . examples/dual-source.typ && typst compile --root . --input mode=note examples/dual-source.typ /tmp/xwysyy-dual-note.pdf`。改主题、脚本或预览时还要跑 `scripts/check-theme-contrast` 与 `scripts/render-visuals /tmp/xwysyy-visual-current && scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current`。
- **视觉基线以 CI 环境为准**：`tests/visual-baseline/` 的判定基准是 workflow 钉死的 CI 字体环境。本机多装字体时，落在示例字体栈之外的字形（含中文的行内代码、⬦ 列表标记等）走系统回退，本地 `compare-png` 会对少数页报已知差异，属正常。更新基线：从 CI run 下载 `visual-current` artifact 覆盖对应 PNG，不要用本地渲染图当基线。
- **文档同步 SOP**：按改动类型查表同步文档，不再维护行号引用。

  | 改了什么 | 必须同步 |
  |---------|---------|
  | 新增/删除/改名公开函数 | README 组件速查 + USAGE 版式/组件章节 + AGENTS 关键文件表 |
	  | 改主题色字段 | README 主题配色表 + CUSTOMIZATION §1 + THEME-GENERATOR |
	  | 改 show rule 行为 | USAGE §9 show 规则速览 |
	  | 改 example deck 结构 | 重新生成 preview PNG + README 预览表 |
	  | 改 CI / preview 脚本 | CUSTOMIZATION 维护命令 + AGENTS 关键文件表 |
	  | 纯内部重构（不改公开 API） | 无 |
	  | 发版 | CHANGELOG.md + typst.toml version + git tag |
- **主题色变量是契约**：`themes` 字典中每套主题的 `sea` / `sky` / `skyl` / `skyll` / `paper` 以及 `header-fill` / `header-text` / `page-fill` 既是颜色定义，也通过 `config-colors` 映射到 touying 的语义槽（`neutral-dark = sea` 等）。改名要同步改 `xwysyy-pre` 内 `config-colors(...)` 调用，否则下游 slide 组件会拿到错误颜色。运行时通过 `_theme-state`（state）向 `textbox` 等组件传播主题色。
- **函数命名前缀**：当前所有公开主题函数前缀为 `xwysyy-`（`xwysyy-pre`、`xwysyy-doc`、`xwysyy-slide`、`xwysyy-elements`、`xwysyy-note`）。新增函数沿用此前缀；`title-slide` / `outline-slide` / `textbox` / `end-slide` 等通用 helper 不带前缀。
- **笔记模式是主题无关的**：`xwysyy-note` 不使用 `themes` 字典或 `_theme-state`，所有颜色为灰度 + 固定蓝色链接。改笔记样式不需要关心 slide 主题系统。
- **typst + touying 边界 bug**：`config-info(author: [])`（空 content）在 typst 0.14 + touying 0.7.3 组合下仍会触发 touying `markup-text` 把空 content 处理成 none，失败于内部类型检查（`@preview/touying:0.7.3/src/slides.typ:37`）。空作者用 `author: " "` 绕开，不要回退到 `[]`。
- **不要随便引入 typst package**：核心依赖只有 `@preview/touying:0.7.3` 与 `@preview/physica:0.9.8`。`xwysyy-extras.typ` 额外依赖 `cetz`/`fletcher`/`theorion`，但它是可选文件不影响核心模板。新增核心依赖前先评估是否可在 `src/` 子模块内手写实现。
- **inline code 与 block code 分开处理**：`xwysyy-elements` 中 `raw.where(block: true)` 用 `block(width: 100%)` 全宽显示，`raw.where(block: false)` 用 `box(baseline: 0.2em)` 内联显示。修改代码样式时需同步改两处。
- **箭头 show rule 用 math 模式**：箭头替换（`->` -> `$->$` 等）必须用 `$...$` 进入 math 模式才能渲染为箭头符号。不要用 `math.limits(it)`（只管上下标位置，不做符号转换）。长箭头（`-->`、`==>`）的 show rule 必须定义在短箭头（`->`、`=>`）之前，否则短规则会先截取。

## 改主题的常见动线

- **改色 / 新增主题**：普通用户直接传 theme 字典；维护内置主题时编辑 `src/themes.typ` 顶部 `themes` 字典，新增一个 key 即可。每个主题需包含 `sea`/`sky`/`skyl`/`skyll`/`paper`/`header-fill`/`header-text`/`page-fill` 共 8 个字段，改完跑 `scripts/check-theme-contrast` 和 `scripts/gen-previews --with-baseline`。
- **改字体 / 语言**：优先通过 `xwysyy-pre(font: ..., code-font: ..., lang: ...)` 或 `xwysyy-doc(...)` 参数设置。改默认字号才编辑 `src/slides.typ` 内 `set text(... size: 5.5mm)`。
- **改 slide 顶部 / 底部装饰**：编辑 `src/slides.typ` 内 `xwysyy-slide` 的 `header(self)` / `footer(self)` 函数。header 使用 `block` 固定高度 2.5em，颜色来自 `config-store` 的 `header-fill`/`header-text`。footer 简化为可选文字 + 页码（无背景/边框）。
- **新增页面版式**：在 `src/slides.typ` 里仿照 `focus-slide` / `end-slide` 写一个 `touying-slide-wrapper` 即可。**必须用 `utils.merge-dicts(self, config-page(...))`，不要用 `show: touying-slides.with(...)`**——后者在 touying 0.7.x 会产生 ghost slide（参见 `title-slide` 实现）。
- **双产物降级**：新增 slide 专属版式时同步考虑 `sys.inputs.at("mode", default: "slides") == "note"` 分支，否则 `xwysyy-doc` 的 note 产物会残留 slide 结构。
- **改 slide show 规则**：编辑 `src/elements.typ` 内 `xwysyy-elements` 的 show 规则块。注意 raw 有 block: true 和 block: false 两条 show rule。
- **改笔记 show 规则**：编辑 `src/note.typ` 内 `xwysyy-note` 函数的对应规则（独立于 slide，不共享 `xwysyy-elements`）。
- **`textbox` 组件**：在 `src/elements.typ` 里。浅色圆角文本框，背景色为当前主题的 `skyll`。单列直接全宽 block；多列模式内部用 `components.lazy-layout` + `components.lazy-v(1fr)` 实现等高。颜色通过 `_theme-state` 读取。

## 本项目不存在的文档（防止 AI 强行创建）

- 没有 `docs/spec.md` — 模板没有"功能需求"，无外部契约
- 没有 `docs/implementation-plan.md` — 没有多步开发任务
- 没有 `docs/feature-flow.md` — 模板就是一组 show 规则集合
- 没有 `docs/architecture.md` — 小型 facade + src 子模块结构
- 没有 `docs/iteration-notes.md` — 单人维护，`git log` 即历史

> `docs/USAGE.md` 和 `docs/CUSTOMIZATION.md` 已存在（见上方"关键文件"表），是用户文档，不在此清单。

## 上游 / 致谢

主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)（MIT），底层基于 [touying](https://github.com/touying-typ/touying)。
