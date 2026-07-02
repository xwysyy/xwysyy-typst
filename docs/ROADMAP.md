# 开发路线图（Roadmap）

> 本文档是交给执行 agent 的实施规划，按 Phase 顺序执行。
> 每个 feature 自带验收标准，全部满足才算完成；动手前先读 §2 现状事实和 §3 全局约束。
> 本文档只定"做什么、验收什么"；具体实现方式在不违反约束的前提下由执行方决定。

---

## 1. 背景与目标

xwysyy-typst 当前版本 0.1.0，已上架 Typst Universe，形态是"作者自用的主题包"：
用户要用它需要手动复制文件，自定义主题需要 fork，touying 的 handout / 讲者备注能力没有暴露。

本路线图的目标：把它从"作者自用主题"变成"陌生人 60 秒内能采用、不 fork 就能定制的模板包"。
分三个 Phase：

| Phase | 主题 | 目标版本 |
|-------|------|---------|
| 1 | 消除采用摩擦（模板化、主题参数化、字体与语言适配） | 0.2.0 |
| 2 | 一份源码多种产物（handout、讲者备注、同源讲义） | 0.3.0 |
| 3 | 信任与可维护性（CI 视觉回归、主题库扩容） | 0.3.x 起持续 |

---

## 2. 现状事实（已核实，执行时不必重新调研）

### 2.1 代码锚点

| 事实 | 位置 |
|------|------|
| `theme` 参数只接受字符串，查硬编码字典 | `src/slides.typ` 中 `xwysyy-pre` 的 `themes.at(theme)` |
| slides 模式字体硬编码（Times New Roman + Noto Serif CJK SC），无参数 | `src/slides.typ` 中 `xwysyy-pre` 的 `set text(font: ...)` |
| `xwysyy-elements` 有 `code-font` 参数，但 `xwysyy-pre` 调用时未传 | `src/slides.typ` 末尾 `show: xwysyy-elements.with(...)` |
| `outline-slide` 标题硬编码中文"目录" | `src/slides.typ` 中 `xwysyy-slide(title: [目录])` |
| 笔记模式 `xwysyy-note` 有 `font` / `code-font` / `lang` 参数（slides 应对齐） | `src/note.typ` |
| `typst.toml` 无 `[template]` 段，`exclude` 列表含 `examples/`、`assets/`、`docs/` | `typst.toml` |
| README 快速开始教用户手动复制 `xwysyy.typ` 和 `src/` | `README.md` §Quick Start |
| `xwysyy.typ` 对 touying 做了星号 re-export（`#import "@preview/touying:0.7.4": *`） | `xwysyy.typ` |
| `xwysyy-pre` 的 `..args` 透传给 `touying-slides.with(...)` | `src/slides.typ` |

### 2.2 Typst Universe 模板包规范（来源：typst/packages 官方 docs/manifest.md）

- `[template]` 段三个字段：`path`（脚手架目录）、`entrypoint`（相对 template path 的编译目标）、`thumbnail`（相对包根）。
- thumbnail 硬性规则：PNG 或无损 WebP；长边不小于 1080px；不超过 3 MiB；必须是"模板初始化后"某一页的真实渲染；包内任何地方不得引用它（发布时自动排除）。
- 官方建议生成命令：`typst compile -f png --pages 1 --ppi 250 main.typ thumbnail.png`。
- 本地测试流程：把仓库 symlink 到本地包目录（Linux 默认 `~/.local/share/typst/packages/preview/xwysyy/<version>`），然后 `typst init @preview/xwysyy:<version>`；未进索引的版本必须显式写版本号。
- 发布方式：向 typst/packages 仓库提 PR。

### 2.3 touying 0.7.x 已具备的能力（来源：touying 仓库，已核实）

- handout 模式：`config-common(handout: true)`；`handout-subslides` 控制保留哪些子页（默认只留末帧）；`<touying:handout>` label 可标记只在 handout 出现的页。
- 讲者备注：`#speaker-note[...]`；双屏显示 `config-common(show-notes-on-second-screen: right)`。
- pdfpc：`enable-pdfpc` 默认开启；导出命令
  `typst query --root . <deck>.typ --field value --one "<pdfpc-file>" > <deck>.pdfpc`。
- 由于 `xwysyy.typ` 星号 re-export touying，`speaker-note`、`config-common` 等很可能已对用户可用。F4 / F5 动手前先验证透传路径是否直接可用，能用则工作量以文档和示例为主，不加多余封装。

---

## 3. 全局约束（每个任务都适用）

1. **改完必编译**：任何对 `xwysyy.typ` / `src/*.typ` / 示例 / 模板脚手架的修改，完成后必须跑通：

   ```bash
   typst compile --root . examples/slides-sky.typ
   typst compile --root . examples/slides-sunset.typ
   typst compile --root . examples/note.typ
   ```

   Phase 2 起新增的示例产物也加入此清单。
2. **视觉回归底线**：凡验收标准写"视觉一致"，用渲染 PNG 逐页像素对比验证，不凭肉眼：

   ```bash
   typst compile --root . examples/slides-sky.typ -f png "before-{p}.png"
   # 改动后渲染 after-{p}.png，逐页对比：
   compare -metric AE before-1.png after-1.png diff-1.png
   ```

3. **文档同步 SOP**：按 `AGENTS.md` 的"文档同步 SOP"表执行（新增公开函数要同步 README 组件速查 + USAGE + AGENTS 关键文件表；发版要同步 CHANGELOG + typst.toml version）。
4. **命名与依赖纪律**：新公开入口函数沿用 `xwysyy-` 前缀，通用 helper 不带前缀；不新增核心依赖（核心只有 touying 与 physica），extras 依赖不动。
5. **touying 已知坑**（详见 AGENTS.md）：新版式必须用 `utils.merge-dicts(self, config-page(...))`，不要在版式内 `show: touying-slides.with(...)`（会产生 ghost slide）；空 author 用 `" "` 不用 `[]`。
6. **Git 安全**：不擅自 commit / push / tag / 新建 branch；禁止任何破坏性 git 操作（reset --hard、checkout .、clean -f、push --force、rebase）。每个 feature 完成后停下，把改动清单和验收结果报给用户，由用户决定提交。
7. **范围纪律**：只做本文档列出的 feature；实现中发现范围外问题，记录并上报，不顺手修。

---

## 4. Phase 1：消除采用摩擦（0.2.0）

### F1 Universe 模板化

**目标**：让 `typst init @preview/xwysyy` 直接可用，进入 Universe 模板画廊；README 不再教用户复制文件。

**改动清单**：

- `typst.toml`：新增 `[template]` 段（`path = "template"`、`entrypoint = "main.typ"`、`thumbnail = "thumbnail.png"`）；确认 `exclude` 列表不误伤 `template/`；version 升到 0.2.0（与 F2 / F3 一起发）。
- 新建 `template/main.typ`：最小可用 deck 脚手架，从 `#import "@preview/xwysyy:0.2.0": *` 导入，内容覆盖封面、目录、一个章节、一页正文（含 textbox 与高亮宏）、结束页。
- 生成 `thumbnail.png`：对初始化后的 `template/main.typ` 首页按 §2.2 规范渲染。
- `README.md` / `README-zh.md`：快速开始改为两种方式（`typst init @preview/xwysyy:0.2.0` 与 `#import "@preview/xwysyy:0.2.0": *`），删除"复制 xwysyy.typ 和 src/"的指引。

**验收标准**：

- [ ] 按 §2.2 的 symlink 流程本地测试：干净目录下 `typst init @preview/xwysyy:0.2.0` 生成项目，`typst compile main.typ` 零警告出 PDF。
- [ ] `thumbnail.png` 满足全部硬性规则：PNG、长边不小于 1080px、不超过 3 MiB、内容与初始化后模板首页一致、包内无任何引用。
- [ ] 两份 README 的快速开始不再出现"复制文件"指引；示例代码里的 import 语句带版本号。
- [ ] 全局约束 1 的编译清单全部通过。

### F2 自定义主题免 fork

**目标**：`docs/THEME-GENERATOR.md` 生成的配色字典可以直接作为参数传入，不再要求用户改包内源码。

**改动清单**：

- `src/slides.typ`：`xwysyy-pre` 的 `theme` 参数同时接受字符串（查内置字典，现行为不变）和字典（直接使用）。传入字典时校验 8 个字段（`sea` / `sky` / `skyl` / `skyll` / `paper` / `header-fill` / `header-text` / `page-fill`）齐全，缺字段时报错并指名缺哪个；`header-fill` / `header-text` 允许为 `none`（回退逻辑不变）。
- `docs/THEME-GENERATOR.md`：使用说明从"粘贴进 src/themes.typ"改为"作为 theme 参数传入"，保留"vendor 用户改 themes.typ"作为备选路径。
- `README.md` / `README-zh.md` / `docs/USAGE.md` / `docs/CUSTOMIZATION.md`：theme 参数说明同步。

**验收标准**：

- [ ] 把 THEME-GENERATOR.md 中 forest 示例字典直接传给 `xwysyy-pre`，编译通过；渲染结果与把同一字典注册进 `themes.typ` 后按名调用的结果逐页像素一致（按全局约束 2 验证）。
- [ ] 自定义颜色在动态组件上生效：header 底色与文字、表格首行、textbox 底色、代码块底色、目录页徽章逐项核对为字典颜色（`_theme-state` 传播路径覆盖到）。
- [ ] 传入缺字段的字典时编译报错，错误信息包含缺失字段名。
- [ ] `theme: "sky"` / `theme: "sunset"` 字符串用法行为与 0.1.0 完全一致（像素对比三个 example）。

### F3 字体参数化与语言适配

**目标**：slides 模式与笔记模式参数对齐；typst.app 网页端（无本地字体）可用；英文 deck 不再出现中文"目录"。

**改动清单**：

- `src/slides.typ`：`xwysyy-pre` 新增 `font`、`code-font`、`lang` 参数，默认值与现状一致（`("Times New Roman", "Noto Serif CJK SC")`、`"Maple Mono"`、`"en"`）；`code-font` 接线到 `xwysyy-elements.with(...)`（现在没传）。
- `src/slides.typ`：`outline-slide` 新增 `title: auto` 参数；`auto` 时按当前 `text.lang` 取"目录"（zh）或 "Contents"（其他），显式传入则用传入值。
- `docs/USAGE.md`、README 组件表：参数说明同步；README 的 Requirements 一节补一句网页端用法（传入网页可用字体即可）。

**验收标准**：

- [ ] 三个 example 不传新参数时，渲染结果与改动前逐页像素一致（回归底线，按全局约束 2 验证）。
- [ ] 传入替代字体（如 `font: ("Libertinus Serif",)`、`code-font: "DejaVu Sans Mono"`）编译通过，正文与代码块字体随之变化。
- [ ] `lang: "en"`（默认）时 `outline-slide()` 标题为 "Contents"；`lang: "zh"` 时为"目录"；显式 `title: [Agenda]` 覆盖生效。
- [ ] `xwysyy-pre` 与 `xwysyy-note` 的字体类参数命名一致。

---

## 5. Phase 2：一份源码多种产物（0.3.0）

### F4 handout 模式打通并文档化

**目标**：用户加一个开关就能把带 `#pause` 的 deck 编译成讲义版（动画折叠为末帧）。

**改动清单**：

- 先验证现有透传：`#show: xwysyy-pre.with(theme: ..., config-common(handout: true), ...)` 是否直接生效。生效则不改代码，以文档和示例为主（最简方案）；不生效才排查 `..args` 透传路径并修复。
- `docs/USAGE.md` 新增 handout 章节：开关用法、`handout-subslides` 取值、`<touying:handout>` label。
- `examples/` 下给出 handout 编译示例（可以是现有 deck 加编译说明，也可以是独立入口文件，取实现最简者）。

**验收标准**：

- [ ] `examples/slides-sky.typ`（含多处 `#pause`）开启 handout 后编译产物中，所有含 `#pause` 的页只剩末帧，PDF 总页数等于逻辑页数。
- [ ] 关闭 handout 时产物与现状一致（像素对比）。
- [ ] USAGE.md 的 handout 章节示例代码可直接复制编译通过。

### F5 讲者备注与 pdfpc 导出

**目标**：用户能写 `#speaker-note`，并导出 `.pdfpc` 文件用于双屏演讲。

**改动清单**：

- 先验证 `#speaker-note` 是否已随星号 re-export 对用户可用（大概率可用）。可用则零代码改动；不可用则在 `xwysyy.typ` 补 re-export。
- `docs/USAGE.md` 新增讲者备注章节：`#speaker-note` 用法、`show-notes-on-second-screen` 选项、§2.3 的 pdfpc 导出命令。
- 任一 example deck 中加入至少一处 `#speaker-note` 作为活示例。

**验收标准**：

- [ ] example 中加 `#speaker-note` 后，deck 渲染结果与不加时逐页像素一致（备注不可见）。
- [ ] `typst query --root . examples/<deck>.typ --field value --one "<pdfpc-file>"` 输出合法 JSON，且包含示例中写入的备注文本。
- [ ] USAGE.md 章节中的命令原样复制可执行。

### F6 slides 与 note 同源双产物（本 Phase 核心，先设计后实现）

**目标**：同一份源码，默认编译出 16:9 deck，加 `--input mode=note` 编译出 A4 讲义。学术场景的典型收益：讲完课直接发讲义，不维护两份内容。

**执行门槛**：这是全路线图唯一有设计难度的 feature。动手写代码前，先产出一页设计稿（写入 PR 描述或临时文档均可）交用户确认，设计稿必须回答：

1. 入口形态：新入口函数（如 `xwysyy-doc`）还是在 `xwysyy-pre` 内分流；如何读 `sys.inputs`。
2. slide 专属版式在 note 模式下的降级规则，逐个明确：`title-slide`（转标题块？）、`outline-slide`（转 `#outline()`？跳过？）、`new-section-slide`（转一级标题？本身由 `=` 触发，note 模式天然是标题）、`focus-slide` / `image-slide` / `end-slide`（跳过还是转换）。
3. `#pause` 在 note 模式的处理（预期等价于 handout 行为：只留完整内容）。
4. `textbox`、高亮宏、箭头替换等共享组件在两种模式下的行为（`textbox` 依赖 `_theme-state`，note 模式无主题，需定回退色）。

**改动清单**（设计确认后）：

- 按设计实现模式分流与降级规则。
- 新增一个双产物 example（一份源码），并把两种编译命令写入 README 与 USAGE。
- 两个产物的编译命令加入全局约束 1 的验证清单。

**验收标准**：

- [ ] 一份 example 源码，仅靠 `--input mode=note` 切换即分别产出 16:9 deck PDF 和 A4 讲义 PDF，源码零修改。
- [ ] 每个 slide 专属版式的降级行为与设计稿文档一字不差（逐版式核对产物）。
- [ ] note 产物中不出现 slide 残留（页码格式、header 底色块、16:9 页面尺寸等）。
- [ ] deck 产物与不引入本 feature 前的同内容 deck 逐页像素一致（不能为了双产物牺牲 slides 质量）。
- [ ] 降级规则写入 USAGE.md。

---

## 6. Phase 3：信任与可维护性（0.3.x 起持续）

### F7 CI 与视觉回归

**目标**：任何改动是否破坏渲染，由 CI 判定，不靠人肉盯 PDF；README 预览图脚本化生成。

**改动清单**：

- 新增 GitHub Actions workflow：固定 typst 版本（与 `typst.toml` 的 `compiler` 字段一致），编译全部 example（含 Phase 2 新增产物），渲染 PNG，与仓库内基线图做像素 diff（阈值可配，建议 ImageMagick `compare -metric AE` 或等价 Python 实现）。
- 字体确定性：CI 环境装不了 Times New Roman（专有字体）。基线图必须在 CI 同一环境生成（首次由 workflow 产出后提交），保证 diff 的两侧字体一致；不要拿本地渲染图当基线。
- 新增 `scripts/gen-previews`（语言不限，Shell 需 shebang）：从 example 渲染 README 预览 PNG，替代手工截图；基线更新走同一脚本加显式命令。
- CONTRIBUTING 级别的说明可并入 AGENTS.md 工作规则（如何更新基线）。

**验收标准**：

- [ ] 对 `src/` 做一个故意的渲染性改动（如改主色）提 PR，CI 失败并上传 diff 图 artifact；revert 后 CI 转绿。
- [ ] 纯文档改动的 PR 不触发视觉回归失败。
- [ ] 基线更新有文档化的单命令流程，执行后 CI 通过。
- [ ] README 预览 PNG 由脚本重新生成后与 README 引用一致（无手工截图残留）。

### F8 主题库扩容（2 套到 5 或 6 套）

**目标**：内置主题覆盖更多常见学术场景（例如深绿、藏青、紫色、灰度打印安全款），每套都通过机器可查的对比度约束。

**改动清单**：

- 用 `docs/THEME-GENERATOR.md` 的工作流生成候选主题，人工挑选后加入 `src/themes.typ`。
- 对比度检查脚本化：建议做法是 `typst query` 一个导出 `#metadata(themes)<themes>` 的小文件拿到 JSON，再用脚本按 WCAG 相对亮度公式校验每套主题的 paper 对 sea、header-text 对 header-fill（含 none 回退后的实际颜色）不低于 4.5:1；接入 F7 的 CI。
- 每套新主题：README 主题表加行、预览图（用 F7 的脚本生成）、CHANGELOG 记录。

**验收标准**：

- [ ] 对比度脚本在 CI 中对 `themes` 字典全量运行；人为塞入一套违规配色时 CI 失败，移除后转绿。
- [ ] 每套新主题用 `theme: "<name>"` 编译 example deck 通过，且 header / 表格 / textbox / 代码块 / 目录徽章颜色正确。
- [ ] README（中英）主题表、预览图、CHANGELOG 三处同步齐全。

---

## 7. 发布 checklist（每个版本执行一遍）

1. `CHANGELOG.md` 补全本版本条目（Keep a Changelog 格式）。
2. `typst.toml` version 更新；模板脚手架与 README 中的 import 版本号同步。
3. 全局约束 1 的编译清单全部通过；F7 就绪后以 CI 绿为准。
4. 按 §2.2 symlink 流程本地验证 `typst init @preview/xwysyy:<新版本>`。
5. 以上全部通过后，把状态报给用户，由用户决定 git tag 与向 typst/packages 提 PR。

---

## 8. 明确不做

- poster 模式、CV 模式：偏离"slides 加 notes"的包定位，如有需求另起包。
- 继续增加 slide 版式：现有 7 种已覆盖学术 deck 骨架，版式数量不驱动采用。
- 脱离 touying 重写：收益与成本不成比例。
- 引入新的核心依赖：见全局约束 4。
