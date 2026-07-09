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
| `src/slides.typ` | slide 入口 `xwysyy-pre` + 双产物入口 `xwysyy-doc` + 6 种版式（`xwysyy-slide`、`title-slide`、`outline-slide`、`new-section-slide`、`image-slide`、`end-slide`）。`outline-slide` 自动过滤 `<touying:hidden>` 标签且 >5 章自动两列，`title: auto` 按 `text.lang` 输出 `Contents` / `目录`。`frozen-counters` 默认冻结 `figure` 和 `math.equation` 计数器 |
| `src/layout.typ` | 语义布局层 + 版面遥测：`duo-slide` / `focus-slide` / `grid-slide` / `stack-slide` / `compare-slide` / `stat-slide` / `figure-slide` / `sidebar-slide`。每个在编译期 `measure` 真实高度、按节奏分配留白、导出 `<xwysyy-slide-layout>` 归一化几何 metadata，并在 note 模式线性降级。`grid`/`compare`/`stat`/`sidebar` 画等高卡片（`card` 参数）；`stat`/`figure` 复用 grid/duo。**新增组件不要把 `context {}` 套在产出 slide 的调用外层**（touying 会 panic，颜色改在内容层用 `context`）。AI 生成契约见 `docs/LAYOUT.md` |
| `src/extras.typ` | `touying-reducer` 包装的 `cetz-canvas` / `fletcher-diagram` + theorion 全套环境导出 |
| `examples/slides-sky.typ` | sky 主题演示 deck |
| `examples/slides-sunset.typ` | sunset 主题演示 deck |
| `examples/note.typ` | 笔记模式演示（主题无关） |
| `examples/theme-preview.typ` | 可通过 `--input theme=<name>` 渲染任意内置主题的预览 deck |
| `examples/dual-source.typ` | `xwysyy-doc` 双产物示例；默认编译 deck，`--input mode=note` 编译 A4 讲义 |
| `examples/layout-demo.typ` | 语义布局层演示：5 个组件的 good 样例 + 3 个 checker 应捕获的 bad 样例（低密度 / 列失衡 / 溢出） |
| `docs/LAYOUT.md` | 语义布局层设计文档 + 组件 API + 遥测 schema + checker 诊断表 + AI 生成契约 |
| `tests/fixtures/layout-dual.typ` | 组件双产物 fixture：slides 与 `--input mode=note` 都要编译过 |
| `tests/test_slide_check.py` | checker 单测（fixture）+ 真编译集成测试（`typst` 在 PATH 时编译 demo→query→断言诊断） |
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
| `scripts/slide-check.py` | 版面遥测 checker：读 `typst query '<xwysyy-slide-layout>'` 输出，报告密度 / 重心 / 语义关系 / 溢出等内容级诊断（标准库，`--format text\|json`、`--strict`、`--error-only`） |
| `scripts/slide-telemetry` | compile → query → check 一条龙 helper：`scripts/slide-telemetry <deck.typ> [check args...]` |
| `scripts/gen-previews` | 重新生成 README preview PNG（基线更新走 `scripts/adopt-baseline`，不要用 `--with-baseline` 的本地渲染当基线） |
| `scripts/render-visuals` | 渲染视觉回归 PNG 集；内部传 `--input visual-ci=true` 以使用 CI 可安装字体 |
| `scripts/compare-png` | 无 ImageMagick 依赖的 PNG 像素比较器，可输出 diff PNG |
| `scripts/adopt-baseline` | 从最近一次 visual-regression run 下载 `visual-current` artifact 全量覆盖视觉基线（需 gh CLI 已登录） |
| `scripts/check-theme-contrast` | 解析 `src/themes.typ` 并检查主题对比度 |
| `.github/workflows/visual-regression.yml` | 编译示例、检查主题对比度、渲染视觉基线并比较 |
| `tests/fixtures/` | 自定义主题、目录标题、字体参数等编译验证 fixture |
| `tests/visual-baseline/` | CI 视觉回归基线 PNG |
| `LICENSE` | MIT，沿用上游 |

## 工作规则（项目层面）

完整开发纪律见 `~/.claude/rules/dev-principles.md` + `dev-protocols.md`；以下是本项目特有提醒。

- **改完必编译**：任何对 `xwysyy.typ` / `src/*.typ` / 示例 / 模板脚手架的修改完成后，至少跑 `typst compile --root . examples/slides-sky.typ && typst compile --root . examples/slides-sunset.typ && typst compile --root . examples/note.typ && typst compile --root . examples/dual-source.typ && typst compile --root . --input mode=note examples/dual-source.typ /tmp/xwysyy-dual-note.pdf`。改主题、脚本或预览时还要跑 `scripts/check-theme-contrast` 与 `scripts/render-visuals /tmp/xwysyy-visual-current && scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current`。
- **改语义布局层必验遥测**：改 `src/layout.typ` / `scripts/slide-check.py` 后跑 `typst compile --root . examples/layout-demo.typ /tmp/layout-demo.pdf && scripts/slide-telemetry examples/layout-demo.typ && python3 -m unittest tests/test_slide_check.py && typst compile --root . --input mode=note tests/fixtures/layout-dual.typ /tmp/layout-note.pdf`。改阈值后必须确认 demo 的 5 个 good 页仍全过、3 个 bad 页仍被捕获（阈值以真实测量的 good 页为锚校准，不要放水让 bad 页蒙混）。
- **视觉基线以 CI 环境为准**：`tests/visual-baseline/` 的判定基准是 workflow 钉死的 CI 字体环境。本机多装字体时，落在示例字体栈之外的字形（含中文的行内代码、⬦ 列表标记等）走系统回退，本地 `compare-png` 会对少数页报已知差异，属正常。更新基线：视觉改动 push 后等 CI 跑完，跑 `scripts/adopt-baseline`（自动下载该 run 的 `visual-current` artifact 全量覆盖 `tests/visual-baseline`），review 后补 `test:` 提交；不要用本地渲染图当基线。
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
- **主题色变量是契约**：`themes` 字典中每套主题必含 6 个字段 `sea` / `sky` / `skyl` / `skyll` / `paper` / `page-fill`（`_resolve-theme` 逐一校验，缺字段 panic）；`header-text` 是可选字段，非 `none` 时覆盖内容页 open header 的标题颜色（默认 `sea`），6 套内置主题均为 `header-text: none`；`header-fill` 字段已删除，不要再写进主题字典。这些字段既是颜色定义，也通过 `config-colors` 映射到 touying 的语义槽（`neutral-dark = sea` 等）；`config-store` 还携带 `heading-font` 与 `header-color`（由 `header-text` 回退到 `sea` 解析而来）供 header 使用。改名要同步改 `xwysyy-pre` 内 `config-colors(...)` 调用，否则下游 slide 组件会拿到错误颜色。运行时通过 `_theme-state`（state）向 `textbox` 等组件传播主题色。
- **函数命名前缀**：当前所有公开主题函数前缀为 `xwysyy-`（`xwysyy-pre`、`xwysyy-doc`、`xwysyy-slide`、`xwysyy-elements`、`xwysyy-note`）。新增函数沿用此前缀；`title-slide` / `outline-slide` / `textbox` / `end-slide` 等通用 helper 不带前缀。
- **笔记模式是主题无关的**：`xwysyy-note` 不使用 `themes` 字典或 `_theme-state`，所有颜色为灰度 + 固定蓝色链接。改笔记样式不需要关心 slide 主题系统。
- **typst + touying 边界 bug**：不要使用 `config-info(author: [])`（空 content），touying 会把空 content 处理成 none，并触发内部类型检查失败。空作者用 `author: " "` 绕开，不要回退到 `[]`。
- **不要随便引入 typst package**：核心依赖只有 `@preview/touying:0.7.4` 与 `@preview/physica:0.9.8`。`xwysyy-extras.typ` 额外依赖 `cetz`/`fletcher`/`theorion`，但它是可选文件不影响核心模板。新增核心依赖前先评估是否可在 `src/` 子模块内手写实现。
- **inline code 与 block code 分开处理**：`xwysyy-elements` 中 `raw.where(block: true)` 用 `block(width: 100%)` 全宽显示，`raw.where(block: false)` 用 `box(inset: (x: 0.3em), outset: (y: 0.2em))` 内联显示（竖向留白用 `outset` 画，不参与 baseline/行高布局；note 模式同款 `outset` 为 0.15em）。修改代码样式时需同步改两处。
- **箭头 show rule 用 math 模式**：箭头替换（`->` -> `$->$` 等）必须用 `$...$` 进入 math 模式才能渲染为箭头符号。不要用 `math.limits(it)`（只管上下标位置，不做符号转换）。长箭头（`-->`、`==>`）的 show rule 必须定义在短箭头（`->`、`=>`）之前，否则短规则会先截取。

## AI 生成排版契约（语义布局层）

> 生成幻灯片内容时（非维护模板本身），间距和位置一律交给 `src/layout.typ` 的语义组件，不手写数值。完整说明见 `docs/LAYOUT.md`。

- **禁止**：手写 `#v(...)` 制造大间距；用 `place` / 绝对坐标控制普通正文；用 `align(bottom)` 把正文推到底部；一页堆多个无约束 block 靠手感排间距。
- **必须**：图文上下用 `duo-slide`；单一结论少内容用 `focus-slide`；多列对等信息用 `grid-slide`；多块同节奏用 `stack-slide`；左右对比用 `compare-slide`；只通过 `mode: compact | balanced | separated` 调密度。
- **反馈驱动，不靠手感**：编译后跑 `scripts/slide-telemetry <deck.typ>`（或 `typst query '<xwysyy-slide-layout>' --field value | scripts/slide-check.py`），按返回的 `content_overflow` / `low_density` / `column_imbalance` / `semantic_pair_split` 等数值诊断修正，不靠"看起来差不多"停止迭代。诊断含义与修法见 `docs/LAYOUT.md` 的诊断表。
- **组件保证间距、checker 判断内容**：组件已用 `measure` + 节奏规则保证间距正确，不会溢出/塌陷；checker 只报组件无法自行决定的内容级问题（太空 / 太满 / 列失衡 / 溢出）。对称留白不是缺陷。

## 改主题的常见动线

- **改色 / 新增主题**：普通用户直接传 theme 字典；维护内置主题时编辑 `src/themes.typ` 顶部 `themes` 字典，新增一个 key 即可。每个主题需包含 `sea`/`sky`/`skyl`/`skyll`/`paper`/`page-fill` 共 6 个必需字段，可选 `header-text` 覆盖 header 标题色，改完跑 `scripts/check-theme-contrast` 和 `scripts/gen-previews`，基线待 CI 跑完用 `scripts/adopt-baseline` 采纳。
- **改字体 / 语言**：优先通过 `xwysyy-pre(font: ..., code-font: ..., lang: ...)` 或 `xwysyy-doc(...)` 参数设置。改默认字号才编辑 `src/slides.typ` 内 `set text(... size: 5.5mm)`。
- **改 slide 顶部 / 底部装饰**：编辑 `src/slides.typ` 内 `xwysyy-slide` 的 `header(self)` / `footer(self)` 函数。header 是开放式（无底色块）：标题用 `config-store` 的 `heading-font`，bold、1.45em，颜色取 `header-color`（主题 `header-text` 覆盖，默认 `sea`），下方一条全宽 0.12em 细线，填充从标题色经 `sky` 向右渐隐、到 92% 宽度处完全透明的渐变；header 块 `inset` 顶部 1.1em，配套的页面顶部 margin 在 `xwysyy-pre` 的 `config-page` 里是 4.35em，两者要一起调。footer 只剩右下角页码（无背景/边框）。
- **新增页面版式**：在 `src/slides.typ` 里仿照 `end-slide` / `image-slide` 写一个 `touying-slide-wrapper` 即可。**必须用 `utils.merge-dicts(self, config-page(...))`，不要用 `show: touying-slides.with(...)`**——后者在 touying 0.7.x 会产生 ghost slide（参见 `title-slide` 实现）。
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
