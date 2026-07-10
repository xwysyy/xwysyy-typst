# xwysyy-typst — AGENTS.md

> AGENTS.md 是给 AI assistant 的导航地图，不是百科。
> 本项目规模小，多数 dev-templates 的标准文档都不存在（见末尾"本项目不存在的文档"）。

---

## 项目本质

- 单仓个人 typst slide 模板 + 笔记模板 + Universe template + 示例（6 套 slide 主题 + 主题无关的笔记模式 + `xwysyy-doc` 双产物模式）
- 单人维护，有 GitHub Actions 视觉回归，无 contributor
- 主题文件 `xwysyy.typ` 派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)（MIT），整体改名为 `xwysyy-*` 前缀

## 必读

- `docs/LAYOUT.md` — 语义布局层契约（schema v3）：typed items、声明式 sizing、fit 四态、遥测字段、checker 诊断表与 AI 生成契约。凡是生成 slide 内容或改 `src/layout.typ` / `scripts/slide-check.py` / `scripts/xwysyy-check`，先读它。

本项目尚无 `docs/project-memo.md`（跨任务铁律 / 偏好沉淀）；当跨会话信号 >=2 条同类时再按 `~/.claude/rules/dev-protocols.md § Project Memo Protocol` 升级创建。

## 关键文件

| 文件 | 作用 |
|------|------|
| `xwysyy.typ` | facade entry，re-export `src/*.typ` 各子模块 + 包级 `physica` / `touying` import + `super-T-as-transpose` show 规则。用户写 `#import "xwysyy.typ": *` 一次拿全 |
| `xwysyy-extras.typ` | shim，re-export `src/extras.typ`（cetz / fletcher / theorion 集成） |
| `src/themes.typ` | `themes` 字典（sky / sunset / forest / midnight / violet / graphite）+ 主题字段校验 `_resolve-theme` + 顶层色变量（`sea` / `sky` / `skyl` / `skyll` / `paper`）+ `_theme-state` + 颜色宏（`red`/`bred`/`yellow`/`byellow`） |
| `src/elements.typ` | 共享 show-chain `xwysyy-elements`（slide 共用）+ `info` + `textbox` |
| `src/note.typ` | 笔记入口 `xwysyy-note`（A4，主题无关，show 规则独立） |
| `src/slides.typ` | slide 入口 `xwysyy-pre` + 双产物入口 `xwysyy-doc` + 6 种版式（`xwysyy-slide`、`title-slide`、`outline-slide`、`new-section-slide`、`image-slide`、`end-slide`）。`outline-slide` 自动过滤 `<touying:hidden>` 标签且 >5 章自动两列，`title: auto` 按 `text.lang` 输出 `Contents` / `目录`。`frozen-counters` 默认冻结 `figure` 和 `math.equation` 计数器 |
| `src/layout.typ` | 语义布局层 + 版面遥测 v3：`duo-slide` / `focus-slide` / `grid-slide` / `stack-slide` / `compare-slide` / `stat-slide` / `figure-slide` / `sidebar-slide`，共用 `_alloc-column`/`_fit-row` 分配器（item min/pref/max/grow + gap min/pref，fit 四态 normal/compressed/tight/overflow，不变量 overflow⇒body_overflow>0；stretch 视觉硬下限 0.28H），note 模式线性降级。所有槽位收 typed items（`visual(fit: "stretch"|"natural")`/`card`/`takeaway`/`plain`，sizing 声明不推断）；必填槽位 none / 渲染为空 / grid<2 列 / stat 缺 value·label / reveal-from 越界 / tuning key·类型·区间违规一律 panic。对象带 frame/preferred/payload(二维)/paint 四框 + 逐轴 sizing；每个真实渲染 subslide 发 `<xwysyy-frame>` 映射（handout 覆盖率安全）。分步展示用 `reveal: true`（callback 式 `utils.uncover`，完整记录末帧导出）；**组件内容里禁用 `#pause`**（marks 进不了 `context`/`layout` 闭包，touying 会 panic）。**新增组件不要把 `context {}` 套在产出 slide 的调用外层**（touying 会 panic，颜色改在内容层用 `context`）。AI 生成契约见 `docs/LAYOUT.md` |
| `src/extras.typ` | `touying-reducer` 包装的 `cetz-canvas` / `fletcher-diagram` + theorion 全套环境导出 |
| `examples/slides-sky.typ` | sky 主题演示 deck |
| `examples/slides-sunset.typ` | sunset 主题演示 deck |
| `examples/note.typ` | 笔记模式演示（主题无关） |
| `examples/theme-preview.typ` | 可通过 `--input theme=<name>` 渲染任意内置主题的预览 deck |
| `examples/dual-source.typ` | `xwysyy-doc` 双产物示例；默认编译 deck，`--input mode=note` 编译 A4 讲义 |
| `examples/layout-demo.typ` | 语义布局层演示：10 个 good 样例（8 组件 + 纯文本 stack + reveal）+ 6 个 checker 应捕获的 bad 样例（低密度 / 小图 / 列失衡 / 空壳卡片 / 双重溢出） |
| `docs/LAYOUT.md` | 语义布局层设计文档 + 组件 API + 遥测 schema v3 + checker 诊断表 + AI 生成契约（随 Universe 包发布） |
| `tests/fixtures/layout-dual.typ` | 组件双产物 fixture：slides 与 `--input mode=note` 都要编译过 |
| `tests/fixtures/layout-fit.typ` | fit 态回归 fixture：sidebar tight 窗口、stretch 视觉饿死型 overflow（不变量 body_overflow>0）、间隙压缩型 compressed |
| `tests/fixtures/layout-handout.typ` | handout 覆盖率回归：手写页在 handout 折叠后仍须报 telemetry_gap（靠 `<xwysyy-frame>` 真实页码） |
| `tests/fixtures/layout-pixel.typ` | 像素交叉验证真阳性：place 逃逸出 frame（render_telemetry_mismatch）与贴边细长 token（edge_ink 行峰值） |
| `tests/fixtures/panic/` | 17 个必须编译失败的反例：必填槽位、空内容、spacer / 裸线条、单列 grid、tuning key/区间、reveal-from、metric 缺失/为空、kind 参数、visual fit、role 白名单、focus reveal、takeaway stretch、sidebar typed item、image-slide 无图 |
| `tests/fixtures/adversarial/` | 外部审查实锤的假绿反例（自动 id 空白首帧、空 stretch 视觉），集成测试断言它们必须 fail |
| `tests/test_slide_check.py` | checker 单测（合成 v4 记录逐诊断覆盖 + fail-closed 解析 + 帧状态机 + rules 叶级校验）+ 真编译集成测试（demo 判定、fit 态、handout 覆盖率、像素真阳性、对抗回归、panic fixtures 两种产物、页头缩放遥测） |
| `examples/refs.bib` | 笔记演示用 BibTeX |
| `template/main.typ` | Universe template 脚手架入口，使用 `#import "@preview/xwysyy:0.4.0": *` |
| `thumbnail.png` | Universe template thumbnail，由 `template/main.typ` 首页渲染生成 |
| `typst.toml` | 包清单：name/version/entrypoint/template/exclude，发版时同步 CHANGELOG |
| `CHANGELOG.md` | 版本变更记录，遵循 Keep a Changelog 格式 |
| `README.md` | 用户视角文档：用法、组件参考、主题系统、兼容性 |
| `docs/USAGE.md` | 完整 API 参考：所有 slide 版式、组件、非 slide 文档入口 |
| `docs/CUSTOMIZATION.md` | 自定义指南 + 配合 touying 0.7.x 高级特性 |
| `docs/THEME-GENERATOR.md` | AI 生成主题字典提示词，默认指导用户直接传给 `theme` 参数 |
| `docs/DUAL-OUTPUT-DESIGN.md` | `xwysyy-doc` 入口形态、note 模式降级规则、pause 语义和共享组件设计 |
| `scripts/slide-check.py` | 版面遥测几何引擎（schema v4，fail-closed 解析：缺字段 / 未知枚举 / 旧 schema 一律 exit 2）：并集面积覆盖指标（container/visual/payload + declared_payload）、fit 四态数值不变量、帧状态机（steps 1..N / handout 末帧 / 孤儿帧 / 重复 id 皆 error）、empty_shell / underfilled_card（只认 measured payload）、二维碰撞 + 有向关系、逐真实渲染帧检查（empty_frame / sparse_frame）、rules 叶级校验、每条诊断带 action、统一 severity 政策表、`--profile agent|human`、`--dump-features`。默认 error 非零退出（`--strict` warning 也非零，`--advisory` 恒零）；遥测为空非零退出。随 Universe 包发布 |
| `scripts/xwysyy-check` | 统一 QA CLI：一次 `typst query "metadata"` 拿全四种 schema → 几何检查 → 像素交叉验证（`--profile agent` 强制渲染像素）：render_telemetry_mismatch（只认当前 reveal 步可见对象的 frame）/ edge_ink 行峰值 / hollow_object（逐对象 payload 墨迹，排除自身卡片填色 `paint_fill`），页面几何来自 frame v2 遥测而非硬编码常量。`scripts/xwysyy-check <deck.typ> [--input k=v] [--profile agent] [--pixels]`。随 Universe 包发布 |
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
- **改语义布局层必验遥测**：改 `src/layout.typ` / `scripts/slide-check.py` / `scripts/xwysyy-check` 后跑 `scripts/xwysyy-check examples/layout-demo.typ; python3 -m unittest discover -s tests && typst compile --root . tests/fixtures/layout-dual.typ /tmp/layout-dual.pdf && typst compile --root . --input mode=note tests/fixtures/layout-dual.typ /tmp/layout-note.pdf`（demo 含故意的 bad 页，检查退出码非零属预期；CI 的 `Layout telemetry tests` 步骤跑同一套单测，其中已含 panic fixtures、handout 覆盖率与像素真阳性）。改阈值后必须确认 demo 的 10 个 good 页仍全过、6 个 bad 页仍被捕获（阈值以真实测量的 good 页为锚校准，不要放水让 bad 页蒙混）。发版前另跑 `scripts/xwysyy-check examples/layout-demo.typ --pixels` 做像素级交叉验证。
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

- **禁止**：手写 `#v(...)` 制造大间距；用 `place` / 绝对坐标控制普通正文；用 `align(bottom)` 把正文推到底部；一页堆多个无约束 block 靠手感排间距；**修改任何组件的 `tuning` 字典**（数字微调属于人工层，`extra.tuned` 会记录，agent profile 下是 error）；**在布局组件内容里用 `#pause` / `#meanwhile` / 全局 `#uncover`**（touying 会 panic，分步展示改用组件的 `reveal: true`）；给 `xwysyy-slide` 传 `kind`（参数已删除，panic；豁免页只能用 `outline-slide` / `title-slide` 等专用版式）；用 spacer / 空字符串 / 裸线条 / `hide(...)` / 空 stretch 视觉填充槽位（编译期 panic 或像素层 `hollow_object` error）。
- **必须**：图文上下用 `duo-slide`；单一结论少内容用 `focus-slide`；多列对等信息用 `grid-slide`；多块同节奏用 `stack-slide`；左右对比用 `compare-slide`；一行关键数字用 `stat-slide`（条目用 `metric(value, label)`）；图配 caption 与结论用 `figure-slide`；窄标签配宽内容用 `sidebar-slide`（body 传纯内容不包 `textbox`）；要撑满的视觉显式写 `visual(...)`（占位 `rect(width: 100%, height: 100%)`，真实图片 `image(width: 100%, height: 100%, fit: "contain")`），固有尺寸的图用 `image(width: 100%)`；分步展示用 `reveal: true`（精确步数用 `reveal-from`，显式值恒优先；focus / sidebar 没有展示步骤）；只通过 `mode: compact | balanced | separated` 调密度。百分比尺寸的内容不包 `visual()` 会因"渲染为空 / 无可测量宽度"直接 panic，这是设计行为。
- **反馈驱动，不靠手感**：编译后跑 `scripts/xwysyy-check <deck.typ> --profile agent`（agent profile 自动含像素交叉验证），按返回诊断的 `action` 修正（`content_overflow` / `margin_squeeze` / `underfilled_card` / `low_density` / `column_imbalance` / `semantic_pair_split` / `telemetry_gap` / `hollow_object` / `header_overflow` 等），不靠"看起来差不多"停止迭代。`report_bug` 类诊断（frame_integrity / orphan_frame / render_telemetry_mismatch / invalid_fit_state）不该靠改内容消掉。诊断含义与修法见 `docs/LAYOUT.md` 的诊断表。
- **组件保证间距、checker 判断内容**：组件已用 `measure` + 声明式 sizing 分配器保证间距正确；checker 只报组件无法自行决定的内容级问题（太空 / 太满 / 空壳卡片 / 列失衡 / 溢出 / 漏遥测）。对称留白不是缺陷（focus 页有意如此）。

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
