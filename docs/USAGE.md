# USAGE — xwysyy-typst 组件 API 参考

本文档列出 `xwysyy.typ` 暴露的所有公开 API，按"主题入口 -> Slide 版式 -> 组件 -> 非 slide 文档"组织。每个 API 含签名、参数、触发方式与最小示例。

快速上手见 [README.md](../README.md)；自定义改色 / 改字 / 加版式见 [CUSTOMIZATION.md](./CUSTOMIZATION.md)。

---

## 1. 安装与引入

`xwysyy.typ` 是单文件主题，直接放在你的项目根目录或子目录下，用相对路径引入：

```typst
#import "xwysyy.typ": *
```

依赖（首次编译会从 typst universe 自动下载）：

- `@preview/touying:0.7.3`
- `@preview/physica:0.9.5`

可选扩展（需要绘图或定理环境时）：

```typst
#import "xwysyy-extras.typ": *
```

额外下载 `cetz:0.5.0`、`fletcher:0.5.8`、`theorion:0.6.0` 及其依赖（版本由 `xwysyy-extras.typ` 管理）。

### 文件结构

```
xwysyy.typ                          # 主题文件
xwysyy-extras.typ                   # 可选扩展（cetz/fletcher/theorion）
examples/
  xwysyy.typ -> ../xwysyy.typ       # 符号链接
  xwysyy-extras.typ -> ../xwysyy-extras.typ
  slides-sky.typ                     # sky 主题示例
  slides-sunset.typ                  # sunset 主题示例
```

编译示例：`typst compile examples/slides-sky.typ`

---

## 2. 主题入口：`xwysyy-pre`

Slide 演示文稿的主入口，应用 touying 配置 + 字体 + 颜色映射 + 主题选择。

### 签名

```typst
#let xwysyy-pre(
  aspect-ratio: "16-9",
  footer: none,
  theme: "sky",
  ..args,
  body,
)
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `aspect-ratio` | `"16-9"` | 页面长宽比，touying 支持 `"16-9"` / `"4-3"` / `"16-10"` 等 |
| `footer` | `none` | 页脚内容，`none` 时不显示页脚文字（仍显示页码） |
| `theme` | `"sky"` | 主题名，当前支持 `"sky"` 和 `"sunset"` |
| `..args` | -- | 透传给 touying 的额外配置（如 `config-info(...)`、`config-common(...)` 覆盖） |
| `body` | -- | 整份 deck 内容 |

### 用法

```typst
#show: xwysyy-pre.with(
  aspect-ratio: "16-9",
  theme: "sunset",
  footer: [我的演讲],
  config-info(
    title: [演示标题],
    subtitle: [副标题],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)
```

> `config-info` 的完整字段（`short-title` / `short-subtitle` / `contact` / `logo` / `extra` 等）由 touying 提供，`xwysyy-pre` 透传不限制。

### 主题系统

`xwysyy-pre` 通过 `theme` 参数从 `themes` 字典中选取配色方案，并通过 `_theme-state` 在运行时向 `textbox` 等组件动态传播颜色。每套主题包含 8 个颜色字段：`sea`/`sky`/`skyl`/`skyll`/`paper`/`header-fill`/`header-text`/`page-fill`。

header 颜色由 `config-store` 中的 `header-fill` / `header-text` 控制。当主题中 `header-fill` 或 `header-text` 为 `none` 时，分别回退到 `sea` 和 `paper`。

---

## 3. Slide 版式

### 3.1 `title-slide` -- 封面页

**签名**：`#let title-slide(..args)`

**触发方式**：显式调用一次。

**渲染内容**：从 `config-info` 的 `title / subtitle / author / institution / date` 读取并按主题色排版。

```typst
#title-slide()
```

需要在某一次调用中临时覆盖标题信息，可传入 named 参数：

```typst
#title-slide(title: [仅本页的临时标题])
```

### 3.2 `outline-slide` -- 目录页

**签名**：`#let outline-slide(chapters: auto)`

**触发方式**：显式调用。

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chapters` | `auto` | `auto` 时自动收集文档中所有 `=` 一级标题；也可手动传入数组 |

默认模式下自动查询文档中所有一级 heading，无需手动维护章节列表：

```typst
#outline-slide()
```

手动指定章节（覆盖自动查询）：

```typst
#outline-slide(chapters: ([引言], [方法], [实验], [结论]))
```

渲染为带主题色圆形编号牌的章节列表，标题显示在 header bar 中。

**自动行为**：

- **过滤 `<touying:hidden>`**（仅 `auto` 模式）：带 `<touying:hidden>` 标签的一级标题不会出现在目录中，但页面本身正常显示。适用于补充页、Q&A 页等不想暴露在目录中的内容。手动传入 `chapters:` 数组时不做过滤。
- **自动两列**：当章节数 > 5 时，自动切换为两列布局（badge 和字号同步缩小），避免溢出。

### 3.3 `xwysyy-slide` -- 内容页（默认版式）

**签名**：`#let xwysyy-slide(title: auto, ..args)`

**触发方式**：`==` 二级标题自动触发；也可显式调用。

```typst
== 页面标题

正文内容。
```

显式调用时可传 `title` 覆盖默认 heading：

```typst
#xwysyy-slide(title: [自定义标题])[
  正文内容。
]
```

页面顶部 header 使用 `block` 固定高度 2.5em，显示当前 slide 标题（无章节标题）。颜色由主题的 `header-fill` / `header-text` 决定。底部 footer 仅含可选的 footer 文字 + 页码（无背景/边框，无总页数）。

### 3.4 `new-section-slide` -- 章节过渡页

**签名**：`#let new-section-slide(self: none, body)`

**触发方式**：`=` 一级标题自动触发。

```typst
= 章节标题
```

渲染为全屏居中的"章节名"页，不显示 body 内容（body 由 touying 在后续 slide 独立渲染）。`xwysyy.typ` 内已通过 `config-common(new-section-slide-fn: new-section-slide)` 接好钩子。

### 3.5 `focus-slide` -- 全屏强调页

**签名**：`#let focus-slide(body)`

**触发方式**：显式调用。

整张 slide 用 `sea` 色作底，`paper` 色文字，2em 加粗居中——适合"中心议题"或"过渡口号"。

```typst
#focus-slide[本系统的核心：知识图谱 + 多步推理]
```

### 3.6 `image-slide` -- 全屏图片页

**签名**：`#let image-slide(body: none, img: none)`

**触发方式**：显式调用。

图片作 page background 充满整页；`body` 作为底部叠加的说明文字（可选）。

```typst
#image-slide(
  img: image("../images/screenshot.png"),
  body: [系统首页 / 主问答界面],
)
```

### 3.7 `end-slide` -- 结束页

**签名**：`#let end-slide(title: [Thank You!], body: none)`

**触发方式**：显式调用，通常放在 deck 末尾。

```typst
#end-slide(
  title: [谢谢！],
  body: [欢迎提问],
)
```

`body` 为 `none` 时仅显示标题；非 `none` 时在标题下加 20% 宽度的强调色短线 + 副标题文字。

---

## 4. 组件

### 4.1 `textbox` -- 浅底圆角文本框

**签名**：

```typst
#let textbox(inset: 0.8em, radius: 0.4em, width: 100%, gutter: 0.6em, ..bodies)
```

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `inset` | `0.8em` | 内边距 |
| `radius` | `0.4em` | 圆角半径 |
| `width` | `100%` | 单列模式下宽度 |
| `gutter` | `0.6em` | 多列模式下列间距 |
| `..bodies` | -- | 1 个 body：单文本框；2+ 个 body：等高分列 |

背景色为当前主题的 `skyll`，通过 `_theme-state` 读取。多列模式内部用 touying 0.7.1+ 的 `components.lazy-layout`，每列自动 append `lazy-v(1fr)`，视觉等高。

**用法**：

```typst
#textbox([
  这是一段说明文字，使用浅色背景突出显示。
])

// 多列等高
#textbox(
  [*列 1 标题*

  内容 A 较短],

  [*列 2 标题*

  内容 B
  比较长
  分多行],

  [*列 3 标题*

  内容 C 中等],
)
```

### 4.2 `info` -- "标签 - 描述"两列项

**签名**：`#let info(something, description)`

**用法**：在非 slide 文档（如简历、信息卡）中渲染左右对齐的一行：

```typst
#info([姓名], [张三])
#info([日期], [2026-05-10])
```

输出：

```
姓名                                                    张三
日期                                              2026-05-10
```

### 4.3 颜色强调宏

| 宏 | 效果 |
|----|------|
| `red(body)` | 红色文字（`#9c1d11`） |
| `bred(body)` | 红色加粗文字（1.1em + 0.02em 描边） |
| `yellow(body)` | 黄色文字（`#d9ad20`） |
| `byellow(body)` | 黄色加粗文字（1.1em + 0.02em 描边） |

用法：

```typst
这是 #red[重要警告] 和 #bred[极其重要的警告]。

注意 #yellow[提示信息] 和 #byellow[加粗提示]。
```

---

## 5. 笔记模式：`xwysyy-note`

简洁的学术笔记排版入口，支持文献引用。独立于 slide 主题系统，以内容为中心。

### 签名

```typst
#let xwysyy-note(
  doc,
  title: none,
  subtitle: none,
  font: ("Times New Roman", "Noto Serif CJK SC"),
  code-font: "Maple Mono",
  base-size: 10pt,
  lang: "en",
)
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `title` | `none` | 文档标题，`none` 时不显示标题块 |
| `subtitle` | `none` | 副标题（日期、作者等） |
| `font` | Times + Noto Serif CJK SC | 正文字体 |
| `code-font` | `"Maple Mono"` | 代码字体 |
| `base-size` | `10pt` | 正文字号 |
| `lang` | `"en"` | 语言 |

### 用法

```typst
#import "xwysyy.typ": *

#show: xwysyy-note.with(
  title: "我的笔记",
  subtitle: "2026年5月",
)

#outline(title: "目录", indent: 1.5em, depth: 2)

= 第一章

正文内容 @some_ref。

#set text(lang: "en")
#bibliography("refs.bib", style: "ieee")
```

### 内置格式

- A4 纸张，2cm 边距，`regular` 字重
- heading 自动编号 `1.1`
- 标题层级用灰度区分（无主题色），H1 有浅灰分隔线
- 列表标记 ❖ / ⬦ / –（灰色）
- 代码块浅灰底，表格灰底表头
- 链接固定蓝色（`#4271ae`），非主题色
- `>|` 引用装饰（浅灰竖条）

---

## 6. Show 规则速览

`xwysyy-elements` 中的 show 规则仅用于 slide 模式（`xwysyy-pre`）。笔记模式（`xwysyy-note`）有独立的规则集。

### Slide 模式 show 规则（`xwysyy-elements`）

| 规则 | 改什么 | 默认行为 |
|------|--------|----------|
| `show strong` | strong（粗体） | `size: 1.1em, stroke: 0.02em`（使用当前文字色描边） |
| `set list` / `set enum` | list（列表） | 自定义标记 (❖)/⬦/-- + 主题色，spacing 1.2em，body-indent 0.8em |
| `show emph` | emph（斜体） | 纯文本时逐字符 synthetic skew（-8deg）适配 CJK；非文本 content 整体 skew（兼容 theorion 等） |
| `show figure.caption` | figure caption | 0.78em + 灰色 |
| `show figure.where(kind: table)` | table caption | 顶部对齐 |
| `show raw.where(block: true/false)` | raw（代码块 + 行内代码） | `skyll` 底 + 圆角，block 全宽 / box 内联 |
| `show link` | link | 下划线 + `sea` 色 |
| 箭头字符串 show rules | 箭头符号 | `->` / `=>` / `<=>` 等，用 math 模式渲染 |
| `set table` / `show table.cell` | table | `sea` 底表头 + `skyll` 底数据行 + 首行白字加粗 |

### 笔记模式的 heading 样式

`xwysyy-note` 为 heading 1-4 级定义了样式：

| 级别 | 样式 |
|------|------|
| `=` | 深灰字 1.25em 加粗 + 浅灰分隔线 |
| `==` | 深灰字 1.15em 加粗 |
| `===` | 深灰字 1.05em 加粗 |
| `====` | 深灰字 1em 加粗 |

这些规则仅作用于笔记模式。slide 模板的页内标题由 `xwysyy-slide` 的 `header(self)` 渲染。

---

## 7. 速查：API 全列表

| 类别 | API | 用法 |
|------|-----|------|
| Slide 入口 | `xwysyy-pre` | `#show: xwysyy-pre.with(theme: "sky", ...)` |
| Slide 版式 | `title-slide` | 显式调用 |
| Slide 版式 | `outline-slide` | 显式调用，自动收集 `=` 标题生成目录 |
| Slide 版式 | `xwysyy-slide` | `==` 隐式 / 显式 |
| Slide 版式 | `new-section-slide` | `=` 隐式 |
| Slide 版式 | `focus-slide` | 显式调用 |
| Slide 版式 | `image-slide` | 显式调用 |
| Slide 版式 | `end-slide` | 显式调用 |
| 组件 | `textbox` | 显式调用，浅底圆角文本框（单列 / 多列等高） |
| 组件 | `info` | 显式调用 |
| 颜色宏 | `red` / `bred` / `yellow` / `byellow` | 行内调用 |
| 笔记入口 | `xwysyy-note` | `#show: xwysyy-note.with(title: [...])` |

主题色变量 `sea` / `sky` / `skyl` / `skyll` / `paper`（sky 主题默认值）也随 `import` 一并暴露，可以在你的 deck 内直接引用做局部装饰。

---

## 8. 可选扩展：`xwysyy-extras.typ`

`xwysyy-extras.typ` 提供 cetz 绘图、fletcher 流程图和 theorion 定理环境的一站式集成。它是独立文件，不影响核心模板的依赖。

### 引入

```typst
#import "xwysyy.typ": *
#import "xwysyy-extras.typ": *
#show: show-theorion
```

### 8.1 `cetz-canvas` -- 带动画的 cetz 绘图

经过 `touying-reducer` 包装的 cetz 画布，支持 `pause` 逐步显示。每步绘图用独立的 `{}` 代码块，步与步之间用 `pause` 分隔：

```typst
#cetz-canvas(
  {
    import cetz.draw: *
    rect((0, 0), (2, 1.5), fill: skyl, stroke: sea)
    content((1, 0.75), [模块 A])
  },
  pause,
  {
    import cetz.draw: *
    rect((4, 0), (6, 1.5), fill: skyl, stroke: sea)
    content((5, 0.75), [模块 B])
  },
  pause,
  {
    import cetz.draw: *
    line((2, 0.75), (4, 0.75), mark: (end: ">"), stroke: sea)
  },
)
```

> 跨步引用：由于每步是独立的绘图调用，不能跨步使用 `name` 锚点引用（如 `"a.right"`），需用坐标代替。

### 8.2 `fletcher-diagram` -- 带动画的流程图

经过 `touying-reducer` 包装的 fletcher 图表：

```typst
#fletcher-diagram(
  node-stroke: sea,
  node-fill: skyll,
  edge-stroke: sea,
  node((0, 0), [输入]),
  pause,
  edge((0, 0), (1, 0), "->", label: [处理]),
  node((1, 0), [输出]),
)
```

`node` 和 `edge` 已作为命名导出，可直接使用。`fletcher` 模块别名也随 star import 导出，可通过 `fletcher.shapes.rect`、`fletcher.shapes.diamond` 等访问节点形状。

### 8.3 theorion 定理环境

`xwysyy-extras.typ` 导出了 theorion 的全部环境：`definition`、`theorem`、`lemma`、`corollary`、`example`、`remark`、`proof` 等。

```typst
#definition(title: "信息熵")[
  对离散随机变量 $X$，其信息熵定义为：
  $ H(X) = -sum_(i=1)^n P(x_i) log_2 P(x_i) $
]

#theorem[
  $H(X) <= log_2 n$，等号成立当且仅当 $X$ 服从均匀分布。
]
```

使用 theorion 时建议冻结定理计数器，防止 `#pause` 动画导致编号重复。注意用户传入的 `frozen-counters` 会**替换**默认值，因此必须同时包含模板默认的计数器：

```typst
#show: xwysyy-pre.with(
  config-common(frozen-counters: (
    counter(figure), counter(math.equation), theorem-counter,
  )),
  ...
)
```

> `xwysyy-pre` 默认冻结 `counter(figure)` 和 `counter(math.equation)`。如果你传入自己的 `frozen-counters`，务必将这两个也一并列入，否则它们的冻结会丢失。
