<h1 align="center">xwysyy</h1>

<p align="center">
  <a href="https://typst.app/universe/package/xwysyy"><img src="https://img.shields.io/badge/Typst%20Universe-available-239dad.svg" alt="Typst Universe"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT%20%2B%20MIT--0-blue.svg" alt="Licenses: MIT and MIT-0"></a>
  <a href="https://typst.app"><img src="https://img.shields.io/badge/Typst-%E2%89%A5%200.14.0-239dad.svg" alt="Typst"></a>
  <a href="https://github.com/touying-typ/touying"><img src="https://img.shields.io/badge/touying-0.7.4-blueviolet.svg" alt="touying"></a>
  <a href="#-主题"><img src="https://img.shields.io/badge/Themes-6%20built--in-ff69b4.svg" alt="Themes"></a>
</p>

<p align="center">
  <b>中文</b> | <a href="https://github.com/xwysyy/xwysyy-typst/blob/v0.4.0/README.md">English</a>
</p>

`xwysyy` 是基于 [touying](https://github.com/touying-typ/touying) 的学术演示与笔记模板。它支持 slide、handout、讲者备注、pdfpc 元数据，以及同一份 Typst 源码生成 16:9 deck 和 A4 讲义。视觉主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)，许可证为 MIT。

## 特性

- 支持 Universe 模板：`typst init @preview/xwysyy:0.4.0` 直接生成可编译 deck。
- 内置 6 套主题：`sky`、`sunset`、`forest`、`midnight`、`violet`、`graphite`。
- `theme` 可直接接收自定义配色字典，用户不需要 fork 包源码。
- slide 与 note 模式共享 `font`、`code-font`、`lang` 参数；slide 模式另有 `heading-font` 控制 header 标题字体。
- handout、`#speaker-note`、pdfpc 导出都有可复制命令和固定标签的源码示例。
- `xwysyy-doc` 默认生成 16:9 deck，使用 `--input mode=note` 生成 A4 讲义。
- 八个语义版式组件（`duo-slide`、`grid-slide`、`figure-slide`、`stat-slide` 等）编译期测量每个块、填满优先分配空间并导出版面遥测，不再手写 `#v()` 间距。
- Universe 模板自带 `scripts/xwysyy-check`，它把一次编译变成数值化版面诊断（每条带可执行修法）并做像素交叉验证；agent profile 是 AI 生成 deck 的交付门禁。

## 预览

渲染预览由[固定标签下的源码示例](https://github.com/xwysyy/xwysyy-typst/tree/v0.4.0/examples)生成。

### 主题

| sky | sunset | forest |
|:---:|:---:|:---:|
| ![Sky theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-sky-p1-01.png) | ![Sunset theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-sunset-p1-01.png) | ![Forest theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-forest-p1-01.png) |

| midnight | violet | graphite |
|:---:|:---:|:---:|
| ![Midnight theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-midnight-p1-01.png) | ![Violet theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-violet-p1-01.png) | ![Graphite theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-theme-graphite-p1-01.png) |

### 组件页

| Sky 封面 | Sky 组件 |
|:---:|:---:|
| ![Sky theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-sky-p1-01.png) | ![Sky theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-sky-p5-05.png) |

| Sunset 封面 | Sunset 组件 |
|:---:|:---:|
| ![Sunset theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-sunset-p1-01.png) | ![Sunset theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-sunset-p5-05.png) |

| 笔记标题 | 笔记代码 | 笔记表格 |
|:---:|:---:|:---:|
| ![Note mode title and TOC](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-note-p1-1.png) | ![Note mode lists and code](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-note-p2-2.png) | ![Note mode tables and quotes](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.4.0/assets/preview-note-p3-3.png) |

## 快速开始

从 Universe 模板创建新项目：

```bash
typst init @preview/xwysyy:0.4.0 my-talk
cd my-talk
typst compile main.typ
```

在已有项目中引入包：

```typst
#import "@preview/xwysyy:0.4.0": *

#show: xwysyy-pre.with(
  theme: "sunset",
  config-info(
    title: [我的演示标题],
    subtitle: [副标题],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()
#outline-slide()

= 章节标题

== 页面标题

正文内容，支持 *粗体* 和 #red[标红强调]。

#textbox(
  [*模块 A*

  第一列内容],

  [*模块 B*

  第二列内容],
)

#end-slide(title: [谢谢！], body: [欢迎提问])
```

## 主题

按名称选择内置主题：

```typst
#show: xwysyy-pre.with(
  theme: "forest",
  config-info(title: [我的演示]),
)
```

直接传入自定义字典：

```typst
#let my-theme = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-text: none,
  page-fill: white,
)

#show: xwysyy-pre.with(
  theme: my-theme,
  config-info(title: [我的演示]),
)
```

主题必须提供 6 个字段，`header-text` 可选：

| 字段 | 用途 |
|------|------|
| `sea` | 主深色，用于 header 标题、链接、表格首行和目录徽章 |
| `sky` | 强调色，也是 header 分隔线的淡出端 |
| `skyl` | 浅色背景 |
| `skyll` | 代码块、表格数据行和 textbox 底色 |
| `paper` | 深色背景上的文字 |
| `header-text` | 可选，覆盖 header 标题颜色，`none` 回退到 `sea` |
| `page-fill` | slide 页面背景 |

## 组件速查

| 类别 | API | 用法 |
|------|-----|------|
| Slide 入口 | `xwysyy-pre` | `#show: xwysyy-pre.with(theme: "sky", ...)` |
| 双产物入口 | `xwysyy-doc` | 默认 deck，`--input mode=note` 生成 A4 讲义 |
| 封面 | `title-slide` | `#title-slide()` |
| 目录 | `outline-slide` | `#outline-slide()` 自动收集章节标题 |
| 内容页 | `xwysyy-slide` | `== 标题` 自动触发 |
| 章节过渡 | `new-section-slide` | `= 标题` 自动触发 |
| 全屏图片 | `image-slide` | `#image-slide(img: image("bg.png"))` |
| 结束页 | `end-slide` | `#end-slide(title: [...])` |
| 版式 · 图文对 | `duo-slide` | 上图下文，测量间距 + 遥测 |
| 版式 · 单焦点 | `focus-slide` | 内容少时单块居中 |
| 版式 · 多列 | `grid-slide` | N 个等高对等列 |
| 版式 · 堆叠 | `stack-slide` | N 块竖排，视觉块撑大或卡片做高 |
| 版式 · 对比 | `compare-slide` | 左右两块顶部对齐读作对比 |
| 版式 · 指标 | `stat-slide` | 一行大数字指标卡片 |
| 版式 · 配图 | `figure-slide` | 图 + 紧贴 caption + 可选 takeaway |
| 版式 · 侧栏 | `sidebar-slide` | 窄标签条 + 宽内容卡片 |
| 文本框 | `textbox` | `#textbox[内容]` 或 `#textbox([列 1], [列 2])` |
| 标红 | `red` / `bred` | `#red[文字]` / `#bred[粗体标红]` |
| 标黄 | `yellow` / `byellow` | `#yellow[文字]` / `#byellow[粗体标黄]` |
| 笔记入口 | `xwysyy-note` | `#show: xwysyy-note.with(title: [...])` |
| 可选扩展加载器 | `xwysyy-extras()` | 按需加载 cetz、fletcher、theorion 集成 |

只有调用 `xwysyy-extras()` 时才会加载绘图与定理环境，因此核心导入仍保持较小的依赖集合：

```typst
#import "@preview/xwysyy:0.4.0": *
#import xwysyy-extras(): *
```

版式组件（`duo-slide`、`focus-slide`、`grid-slide`、`stack-slide`、`compare-slide`、`stat-slide`、`figure-slide`、`sidebar-slide`）接受声明了 sizing 的 typed item（`visual` / `card` / `takeaway` / `plain` / `metric`），编译期测量每个块、填满优先分配空间，并导出 `<xwysyy-slide-layout>` v4 遥测（每对象带分配框、自然外框、区分测量与声明来源的二维 payload 框、卡片色块框与填色）。通过 `typst init` 创建的项目自带 `scripts/xwysyy-check`；运行 `scripts/xwysyy-check main.typ --profile agent` 可生成数值化诊断并用真实渲染像素交叉验证遥测。分步展示用组件的 `reveal: true`，不要在组件内容里写 `#pause`（touying 会 panic）。详见 [`docs/LAYOUT.md`](docs/LAYOUT.md)。

## Handout 与讲者备注

通过 `xwysyy-pre` 传入 touying 的 handout 设置。命令行开关可以这样接入：

```typst
#let handout = sys.inputs.at("handout", default: "false") == "true"

#show: xwysyy-pre.with(
  config-common(handout: handout),
  config-info(title: [我的演示]),
)
```

```bash
typst compile main.typ slides.pdf
typst compile --input handout=true main.typ slides-handout.pdf
```

`xwysyy.typ` 已 re-export touying，可直接写讲者备注：

```typst
#speaker-note[
  这里提醒自己讲 ablation 表。
]
```

导出 pdfpc 元数据：

```bash
typst query main.typ --field value --one "<pdfpc-file>" > slides.pdfpc
```

## 一份源码，两种产物

需要同一份源码同时生成 slide 和 A4 讲义时使用 `xwysyy-doc`：

```typst
#import "@preview/xwysyy:0.4.0": *

#show: xwysyy-doc.with(
  title: [One Source, Two Outputs],
  subtitle: [Deck and A4 notes],
  theme: "forest",
)
```

编译 deck：

```bash
typst compile main.typ slides.pdf
```

编译 A4 讲义：

```bash
typst compile --input mode=note main.typ notes.pdf
```

## 环境要求

- Typst >= 0.14.0
- touying 0.7.4，首次编译自动下载
- physica 0.9.8，首次编译自动下载
- 默认本地字体：Times New Roman、Noto Serif CJK SC、Libertinus Sans、Noto Sans CJK SC、Maple Mono、Noto Sans Mono CJK SC
- Typst 网页端可通过 `font:`、`heading-font:` 和 `code-font:` 传入网页端可用字体

完整 API 见 [docs/USAGE.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.4.0/docs/USAGE.md)。自定义指南见 [docs/CUSTOMIZATION.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.4.0/docs/CUSTOMIZATION.md)。配色生成器见 [docs/THEME-GENERATOR.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.4.0/docs/THEME-GENERATOR.md)。

## 致谢

- 主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)，许可证为 MIT
- 底层框架为 [touying](https://github.com/touying-typ/touying)

## License

`template/` 以外的文件使用 [MIT](./LICENSE) 许可证。`template/` 内的文件
使用 [MIT-0](./LICENSE-MIT-0) 许可证；从模板创建的项目可以修改和重新
分发，无需署名或附带许可证文本。
