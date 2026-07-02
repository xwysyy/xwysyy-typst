<h1 align="center">xwysyy</h1>

<p align="center">
  <a href="https://typst.app/universe/package/xwysyy"><img src="https://img.shields.io/badge/Typst%20Universe-available-239dad.svg" alt="Typst Universe"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://typst.app"><img src="https://img.shields.io/badge/Typst-%E2%89%A5%200.14.2-239dad.svg" alt="Typst"></a>
  <a href="https://github.com/touying-typ/touying"><img src="https://img.shields.io/badge/touying-0.7.3-blueviolet.svg" alt="touying"></a>
  <a href="#-主题"><img src="https://img.shields.io/badge/Themes-6%20built--in-ff69b4.svg" alt="Themes"></a>
</p>

<p align="center">
  <b>中文</b> | <a href="README.md">English</a>
</p>

`xwysyy` 是基于 [touying](https://github.com/touying-typ/touying) 的学术演示与笔记模板。它支持 slide、handout、讲者备注、pdfpc 元数据，以及同一份 Typst 源码生成 16:9 deck 和 A4 讲义。视觉主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)，许可证为 MIT。

## 特性

- 支持 Universe 模板：`typst init @preview/xwysyy:0.3.0` 直接生成可编译 deck。
- 内置 6 套主题：`sky`、`sunset`、`forest`、`midnight`、`violet`、`graphite`。
- `theme` 可直接接收自定义配色字典，用户不需要 fork 包源码。
- slide 模式与 note 模式的字体参数一致：`font`、`code-font`、`lang`。
- handout、`#speaker-note`、pdfpc 导出都有可复制命令和示例覆盖。
- `xwysyy-doc` 默认生成 16:9 deck，使用 `--input mode=note` 生成 A4 讲义。
- CI 脚本覆盖示例编译、视觉回归、主题对比度检查和 README 预览图生成。

## 预览

```bash
typst compile --root . examples/slides-sky.typ
typst compile --root . examples/slides-sunset.typ
typst compile --root . examples/note.typ
typst compile --root . examples/dual-source.typ
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

### 主题

| sky | sunset | forest |
|:---:|:---:|:---:|
| ![Sky theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-sky-p1-01.png) | ![Sunset theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-sunset-p1-01.png) | ![Forest theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-forest-p1-01.png) |

| midnight | violet | graphite |
|:---:|:---:|:---:|
| ![Midnight theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-midnight-p1-01.png) | ![Violet theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-violet-p1-01.png) | ![Graphite theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-theme-graphite-p1-01.png) |

### 组件页

| Sky 封面 | Sky 组件 |
|:---:|:---:|
| ![Sky theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-sky-p1-01.png) | ![Sky theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-sky-p5-05.png) |

| Sunset 封面 | Sunset 组件 |
|:---:|:---:|
| ![Sunset theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-sunset-p1-01.png) | ![Sunset theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-sunset-p5-05.png) |

| 笔记标题 | 笔记代码 | 笔记表格 |
|:---:|:---:|:---:|
| ![Note mode title and TOC](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-note-p1-1.png) | ![Note mode lists and code](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-note-p2-2.png) | ![Note mode tables and quotes](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/master/assets/preview-note-p3-3.png) |

## 快速开始

从 Universe 模板创建新项目：

```bash
typst init @preview/xwysyy:0.3.0 my-talk
cd my-talk
typst compile main.typ
```

在已有项目中引入包：

```typst
#import "@preview/xwysyy:0.3.0": *

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
#show: xwysyy-pre.with(theme: "forest", ...)
```

直接传入自定义字典：

```typst
#let my-theme = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-fill: none,
  header-text: none,
  page-fill: white,
)

#show: xwysyy-pre.with(theme: my-theme, ...)
```

每套主题包含 8 个字段：

| 字段 | 用途 |
|------|------|
| `sea` | 主深色，用于 header、链接、表格首行、目录徽章和 focus slide |
| `sky` | 强调色 |
| `skyl` | 浅色背景 |
| `skyll` | 代码块、表格数据行和 textbox 底色 |
| `paper` | 深色背景上的文字 |
| `header-fill` | header 背景，`none` 回退到 `sea` |
| `header-text` | header 文字，`none` 回退到 `paper` |
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
| 焦点页 | `focus-slide` | `#focus-slide[大字内容]` |
| 全屏图片 | `image-slide` | `#image-slide(img: image("bg.png"))` |
| 结束页 | `end-slide` | `#end-slide(title: [...])` |
| 文本框 | `textbox` | `#textbox[内容]` 或 `#textbox([列 1], [列 2])` |
| 标红 | `red` / `bred` | `#red[文字]` / `#bred[粗体标红]` |
| 标黄 | `yellow` / `byellow` | `#yellow[文字]` / `#byellow[粗体标黄]` |
| 笔记入口 | `xwysyy-note` | `#show: xwysyy-note.with(title: [...])` |
| 可选扩展 | `xwysyy-extras` | cetz、fletcher、theorion 集成 |

## Handout 与讲者备注

`examples/slides-sky.typ` 读取 `--input handout=true` 并传给 touying：

```bash
typst compile --root . examples/slides-sky.typ slides.pdf
typst compile --root . --input handout=true examples/slides-sky.typ slides-handout.pdf
```

`xwysyy.typ` 已 re-export touying，可直接写讲者备注：

```typst
#speaker-note[
  这里提醒自己讲 ablation 表。
]
```

导出 pdfpc 元数据：

```bash
typst query --root . examples/slides-sky.typ --field value --one "<pdfpc-file>" > slides-sky.pdfpc
```

## 一份源码，两种产物

需要同一份源码同时生成 slide 和 A4 讲义时使用 `xwysyy-doc`：

```typst
#import "@preview/xwysyy:0.3.0": *

#show: xwysyy-doc.with(
  title: [One Source, Two Outputs],
  subtitle: [Deck and A4 notes],
  theme: "forest",
)
```

编译 deck：

```bash
typst compile --root . examples/dual-source.typ dual-slides.pdf
```

编译 A4 讲义：

```bash
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

## 环境要求

- Typst 0.14.2
- touying 0.7.3，首次编译自动下载
- physica 0.9.8，首次编译自动下载
- 默认本地字体：Times New Roman、Noto Serif CJK SC、Maple Mono
- Typst 网页端可通过 `font:` 和 `code-font:` 传入网页端可用字体

## 维护命令

重新生成 README 预览图：

```bash
scripts/gen-previews
```

重新生成视觉回归基线：

```bash
scripts/gen-previews --with-baseline
```

完整 API 见 [docs/USAGE.md](docs/USAGE.md)。自定义指南见 [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md)。配色生成器见 [docs/THEME-GENERATOR.md](docs/THEME-GENERATOR.md)。

## 致谢

- 主题派生自 [Carlos-Mero/may](https://github.com/Carlos-Mero/may)，许可证为 MIT
- 底层框架为 [touying](https://github.com/touying-typ/touying)

## License

[MIT](./LICENSE)
