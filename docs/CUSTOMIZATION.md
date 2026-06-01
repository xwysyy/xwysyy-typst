# CUSTOMIZATION — xwysyy-typst 自定义指南

本文档讲两件事：

1. **改主题本身**——颜色 / 字体 / 字号 / 版式 / show 规则。所有改动都在 `src/*.typ` 内进行（按职责拆分见 [USAGE.md §1](./USAGE.md#1-安装与引入)），不要在 deck（`examples/slides-sky.typ` 等）里 hack。
2. **配合 touying 0.7.x 高级特性**——动画、双产物、演讲备注、数学环境等，这些写在 deck 里。

API 速查见 [USAGE.md](./USAGE.md)；快速上手见 [../README.md](../README.md)。

---

## 1. 改主题色

### 主题字典

`themes` 字典定义了 `sky` 和 `sunset` 两套配色。每套主题包含 8 个颜色字段：

```typst
#let themes = (
  sky: (
    sea: rgb("#3b60a0"),
    sky: rgb("#bdd0f1"),
    skyl: rgb("#eff3ff"),
    skyll: rgb("#f4f9ff"),
    paper: rgb("#f5f6f8"),
    header-fill: none,       // none 时回退到 sea
    header-text: none,       // none 时回退到 paper
    page-fill: white,
  ),
  sunset: (
    sea: rgb("#970014"),
    sky: rgb("#D8A6A2"),
    skyl: rgb("#fdf0f0"),
    skyll: rgb("#FFF8F6"),
    paper: rgb("#f5f6f8"),
    header-fill: rgb("#F7EEE7"),
    header-text: rgb("#970014"),
    page-fill: rgb("#fffefd"),
  ),
)
```

修改现有配色或新增主题，编辑这个字典即可。整套主题（heading 块、表格、文本框、链接、header / footer、页面背景）会全部跟着变，**不需要改其他地方**。

新增主题只需加一个 key：

```typst
sunset: (...),
forest: (
  sea: rgb("#2d6a4f"),
  sky: rgb("#b7e4c7"),
  ...
),
```

然后在 deck 中使用 `theme: "forest"`。

### 与 touying 语义槽的映射

`xwysyy-pre` 内 `config-colors(...)` 把主题变量映射到 touying 的语义颜色槽：

| xwysyy 变量 | touying 语义槽 | 用在哪 |
|------|----------|--------|
| `sea` | `neutral-dark` | 章节标题块、focus-slide 背景、表格首行 |
| `sky` | `primary` | end-slide 强调短线、touying 内部 primary 元素 |
| `skyl` | `neutral-light` | 保留 |
| `skyll` | `neutral-lighter` | 章节页内嵌块、image-slide 标题块 |
| `paper` | `neutral-lightest` | 深色块上的浅色文字 |

额外字段通过 `config-store` 传递给 slide 组件：

| 字段 | 用在哪 |
|------|--------|
| `header-fill` | header 背景色（`none` 时回退 `sea`） |
| `header-text` | header 文字色（`none` 时回退 `paper`） |
| `page-fill` | 页面背景色 |

如果你给主题改了根本不同的色调，建议保持"`sea` 是最深的、`paper` 是最浅的"这条单调性——`src/elements.typ` 内多处 show 规则（如 strong 描边、表格首行）都假设 `sea` 是深色。

### 动态组件颜色

`textbox` 通过 `_theme-state` 在运行时获取当前主题颜色，而非使用固定的全局变量。这意味着切换主题时组件会自动适配新配色。

### 局部使用色变量

全局暴露的 `sea` / `sky` / `skyl` / `skyll` / `paper` 始终是 sky 主题的值，deck 内可以直接引用做局部装饰：

```typst
#text(fill: sea)[*重点*]

#rect(fill: skyll, inset: 0.5em)[备注内容]
```

---

## 2. 改字体 / 字号 / 语言

### Slide 文档（`xwysyy-pre`）

字体设置在 `xwysyy-pre` 函数内：

```typst
set text(
  font: ("Times New Roman", "Noto Serif CJK SC"),
  lang: "en",
  size: 5.5mm,
  weight: "semibold",
  style: "normal",
)
```

要改字体或字号，直接编辑这块。注意 `font` 是数组——前者是西文 fallback，后者是中文 fallback，缺字时会逐个回退。

也可以在 deck 里临时覆盖：

```typst
#show: xwysyy-pre.with(...)

#set text(size: 6.5mm)  // 覆盖整份 deck 的字号
```

### 笔记模式（`xwysyy-note`）

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

所有参数均可在 `#show: xwysyy-note.with(...)` 中覆盖：

```typst
#show: xwysyy-note.with(
  title: "自定义标题",
  font: ("Libertinus Serif", "LXGW WenKai"),
  base-size: 11pt,
  lang: "zh",
)
```

### 中文环境提示

`lang: "zh"` 会让 typst 启用 CJK 段落规则（标点挤压、行尾标点处理）。Slide 默认是 `lang: "en"`，混排中文时不会出大问题但段落首行不缩进——需要的话改成 `lang: "zh"`。

### 改 code-font（代码字体）

Slide 模式：`xwysyy-elements` 接受 `code-font` 参数（默认 `"Maple Mono"`）。

笔记模式：`xwysyy-note` 的 `code-font` 参数可直接覆盖：

```typst
#show: xwysyy-note.with(code-font: "JetBrains Mono")
```

---

## 3. 改 aspect-ratio

`xwysyy-pre(aspect-ratio: ...)` 已经是参数化的，默认 `"16-9"`。touying 支持任意比例：

```typst
#show: xwysyy-pre.with(
  aspect-ratio: "16-10",  // 也可 "4-3" / "3-2" / "21-9" 等
  ...
)
```

如果改了非 16:9 比例后发现内容溢出（slide 高度变化导致 footer 顶不上去之类），调整 `xwysyy-pre` 中 `config-page` 的 `margin`：

```typst
config-page(
  paper: "presentation-" + aspect-ratio,
  margin: (top: 3.7em, x: 1em, bottom: 1.4em),  // 改这里
),
```

---

## 4. 改 header / footer 装饰

Slide header / footer 在 `xwysyy-slide` 函数体内定义。

### 改 header

`xwysyy-slide` 内的 `header(self)` 函数：

```typst
let header(self) = {
  set align(top)
  block(
    width: 100% + 2em,
    height: 2.5em,
    fill: self.store.header-fill,
    inset: (x: 1em),
    {
      set align(horizon)
      text(fill: self.store.header-text, weight: "extrabold", size: 1.56em, {
        // 显示 slide 标题
      })
    }
  )
}
```

header 使用 `block` 固定高度 2.5em，颜色来自 `config-store` 的 `header-fill` / `header-text`（可通过主题 `themes` 字典自定义）。只显示当前 slide 标题（不显示章节标题）。

常见改法：

- **去掉 header**：在 `xwysyy-slide` 的 `config-page(...)` 中把 `header: header` 删掉，slide 顶部留白
- **加 logo**：在 header 的 `block` 内部添加 `align(left, image("logo.png", height: 1.2em))`
- **改 header 高度**：调整 `height: 2.5em` 的值

### 改 footer

`xwysyy-slide` 内的 `footer(self)` 函数：

```typst
let footer(self) = {
  set align(bottom)
  set text(fill: self.colors.neutral-dark, size: .9em)
  block(
    inset: (x: 0.5em, bottom: 0.4em),
    {
      utils.call-or-display(self, self.store.footer)
      h(1fr)
      context utils.slide-counter.display()
    }
  )
}
```

footer 无背景色/边框，仅显示可选的 footer 文字（左侧）和当前页码（右侧，无总页数）。默认 `footer: none` 时左侧为空。

常见改法：

- **隐藏页码**：删掉 `context utils.slide-counter.display()`
- **加日期**：footer 块里 `h(1fr) + utils.display-info-date(self)`
- **改样式**：`set text(fill: ..., size: ...)` 在 footer 块开头

---

## 5. 加新页面版式

仿照 `focus-slide` 写一个最小 `touying-slide-wrapper`：

```typst
#let warning-slide(body) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(
      fill: rgb("#ffe5e5"),  // 浅红底
      margin: 0em,
    ),
  )
  set text(fill: rgb("#a00000"), size: 2em, weight: "bold")
  touying-slide(self: self, align(horizon + center, body))
})
```

deck 里调用：

```typst
#warning-slide[这是一个非常重要的提醒！]
```

> **重要**：所有自定义版式必须用 `utils.merge-dicts(self, config-page(...))` 而非 `show: touying-slides.with(config-page(...))`——后者在 touying 0.7.x 会产生 ghost slide。`src/slides.typ` 里的所有版式都是前者写法，照抄即可。

---

## 6. 改 show 规则（strong / list / italic / table / figure / link）

文档级 show 规则集中在 `xwysyy-elements` 函数中。

| 规则 | 改什么 | 默认行为 |
|------|--------|----------|
| `show strong` | strong（粗体） | `stroke: 0.04em`（使用当前文字色描边，不改变字号，非默认 bold） |
| `set list` / `set enum` | list（列表） | 自定义标记 (❖)/⬦/--，sea/sky 主题色，spacing 1.2em，body-indent 0.8em |
| `show emph` | emph（斜体） | 纯文本时逐字符 synthetic skew（-8deg）适配 CJK；非文本 content 整体 skew（兼容 theorion 等） |
| `show figure.caption` | figure caption | 0.78em + 灰色 |
| `show figure.where(kind: table)` | table caption | 顶部对齐 |
| `show raw.where(block: true)` | raw（代码块） | `skyll` 底 + 0.5em 圆角 + 0.6em 内边距，`block(width: 100%)` 全宽 |
| `show raw.where(block: false)` | raw（行内代码） | `skyll` 底 + 0.3em 圆角，`box(baseline: 0.2em)` 内联显示，字号与正文一致 |
| `show link` | link | 下划线 + `sea` 色 |
| 箭头字符串 show rules | 箭头符号 | `->` / `=>` / `<=>` 等，用 `$->$` 风格的 math 模式渲染为数学箭头符号 |
| `set table` | table 样式 | `sea` 底表头 + `skyll` 底数据行 |
| `show table.cell` | table cell | 首行 `paper` 色白字加粗 |

> **行内代码 vs 代码块**：两者使用不同 show rule。行内代码（`` `code` ``）用 `box` 保持内联流，`baseline: 0.2em` 确保与正文垂直对齐；代码块（` ```lang ... ``` `）用 `block(width: 100%)` 独占一行。修改代码样式时需同步改两处。

举例：把代码块底色改成更深的灰：

```typst
// 代码块 show rule
#show raw.where(block: true): it => {
  set text(font: code-font, size: 0.9em)
  block(
    width: 100%,
    height: auto,
    fill: rgb("#1e1e1e"),  // 改这里：深色底
    inset: 0.6em,
    radius: 0.5em,
    text(fill: rgb("#d4d4d4"), it),  // 同步改文字色
  )
}

// 行内代码 show rule（记得同步改）
#show raw.where(block: false): it => {
  set text(font: code-font)
  box(
    fill: rgb("#2d2d2d"),
    inset: (x: 0.3em, y: 0.2em),
    radius: 0.3em,
    baseline: 0.2em,
    text(fill: rgb("#d4d4d4"), it),
  )
}
```

### 笔记模式的 heading 样式

`xwysyy-note` 内置 heading 1-4 级样式（灰度色系，无主题色）。改某级样式，编辑 `xwysyy-note` 函数内对应的 `#show heading.where(level: N)` 块。

---

## 7. 配合 touying 0.7.x 高级特性

以下都写在你的 deck（`examples/slides-sky.typ` 等）里，不需要改主题。

### 7.1 增量揭示（pause / meanwhile / uncover / only）

```typst
== 渐进式揭示

第一步：观察现象。
#pause

第二步：提出假设。
#pause

第三步：验证。
```

更精细的控制：

```typst
- 永远显示
- #uncover("2-")[第二步起出现]
- #only("3")[只在第三步出现]
- #alternatives[版本 A][版本 B][版本 C]
```

详见 [touying 官方动画文档](https://touying-typ.github.io/)。

### 7.2 列表逐项动画

```typst
#show: components.item-by-item

== 演化路径

- 第一阶段：单轮检索
- 第二阶段：多轮迭代
- 第三阶段：自适应规划
```

`#show: components.item-by-item` 之后所有列表 / 枚举 / 术语都按项递进。要回退到普通列表，用 scope 包起来：

```typst
{
  show: components.item-by-item
  - A
  - B
  - C
}
```

### 7.3 代码逐行揭示

讲算法时让代码按行 / 按段递进高亮：

```typst
#touying-raw(
  ```python
  def fib(n):
      if n < 2:
          return n
      return fib(n-1) + fib(n-2)
  ```
)
```

配合 `@preview/codly` 包可以做更精细的高亮。

### 7.4 演讲版 / 讲义版双产物

```typst
== 实验结果

主结论已展示。

#handout-only[
  讲义版补充：详细 ablation 表 + 训练曲线。
]
```

编译时通过 `--input` 切换：

```bash
typst compile --root . examples/slides-sky.typ                             # 演讲版
typst compile --root . --input handout=true examples/slides-sky.typ slides-handout.pdf  # 讲义版
```

> 需要在 `xwysyy-pre` 内加 `config-common(handout: sys.inputs.at("handout", default: "false") == "true")`，否则 `#handout-only` 始终隐藏。本主题默认未加，按需自行扩展。

### 7.5 演讲者备注

```typst
== 实验结果

主结论展示。

#speaker-note[
  这里要强调：本系统在高难度子集上的提升来自图谱推理路径。
  对照实验数据见上一页表格。
]
```

配合 [pdfpc](https://pdfpc.github.io/)：

```bash
typst query examples/slides-sky.typ '<pdfpc-file>' --field value > slides.pdfpc
pdfpc examples/slides-sky.pdf  # 双屏：当前页 + 备注 + 计时
```

详见 [touying speaker notes 文档](https://touying-typ.github.io/)。

---

## 8. 数学环境

### 8.1 physica（已内置）

`xwysyy.typ` 已经 `import "@preview/physica:0.9.8": *`，所有 physica 提供的数学命令在你的 deck 里直接可用：

```typst
$ A^TT $    // 转置：A^T，已通过 super-T-as-transpose show 规则启用
$ tensor(R, +i, -j) $   // 张量
$ pderivative(f, x) $   // 偏导数
$ vbar(0)$ >            // 矢量
```

完整命令列表见 [physica 文档](https://typst.app/universe/package/physica)。

### 8.2 theorion（数学定理环境）

通过 `xwysyy-extras.typ` 提供一站式集成，无需手动管理依赖：

```typst
#import "xwysyy.typ": *
#import "xwysyy-extras.typ": *
#show: show-theorion

#show: xwysyy-pre.with(
  // 用户传入的 frozen-counters 会替换默认值，需同时保留模板默认的计数器
  config-common(frozen-counters: (
    counter(figure), counter(math.equation), theorem-counter,
  )),
  ...
)
```

之后即可使用 `#definition`、`#theorem`、`#lemma`、`#corollary`、`#proof`、`#example`、`#remark` 等环境。

```typst
#definition(title: "信息熵")[
  对离散随机变量 $X$，其信息熵定义为 $H(X) = -sum P(x_i) log_2 P(x_i)$。
]

#theorem[等号成立当且仅当 $X$ 服从均匀分布。]
```

详见 [theorion 文档](https://typst.app/universe/package/theorion) 和 [USAGE.md §8](./USAGE.md#8-可选扩展xwysyy-extrastyp)。

### 8.3 cetz / fletcher（绘图与流程图）

同样通过 `xwysyy-extras.typ` 提供，支持 `#pause` 逐步绘图动画：

```typst
#import "xwysyy-extras.typ": *

// cetz 绘图
#cetz-canvas({
  import cetz.draw: *
  line((0, 0), (3, 2), mark: (end: ">"))
})

// fletcher 流程图
#fletcher-diagram(
  node((0, 0), [A]),
  edge((0, 0), (1, 0), "->"),
  node((1, 0), [B]),
)
```

详细用法和 `pause` 动画语法见 [USAGE.md §8](./USAGE.md#8-可选扩展xwysyy-extrastyp)。

---

## 9. 升级 touying 版本时的注意点

主题用了 touying 0.7.x 的几个特性：

- `components.lazy-layout` + `components.lazy-v(1fr)`（`textbox` 多列分支使用）
- `utils.merge-dicts(self, config-page(...))`（所有 slide 版式都用这个，避免 ghost slide）

跨大版本（如未来升 0.8.x）时优先验证：

1. **编译 `examples/slides-sky.typ`** 看页数和 baseline 一致
2. **多列 `textbox` 页**确认仍然等高
3. **title 页**前后没有空白页（说明 ghost slide 修复仍然有效）

如果 touying 改了 `lazy-layout` 或 `merge-dicts` 语义，按 [USAGE.md](./USAGE.md) 列的 API 与 [touying changelog](https://github.com/touying-typ/touying/releases) 对照修订。
