#import "../xwysyy.typ": *

#let handout-mode = sys.inputs.at("handout", default: "false") == "true"
#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }
#let visual-code-font = if visual-ci { "DejaVu Sans Mono" } else { "Maple Mono" }

#show: xwysyy-pre.with(
  font: visual-font,
  code-font: visual-code-font,
  config-common(handout: handout-mode),
  config-info(
    title: [xwysyy 主题功能演示],
    subtitle: [Typst Slide 模板 · 组件速览],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()

#outline-slide(title: [目录])

// ═══════════════════════════════════════════
= 基础排版

== 文本与强调

这是一段普通正文，用于展示#red[默认字体、字号与行距的效果]。

#pause

#speaker-note[
  这页展示基础文本、强调宏和列表样式。handout 模式只保留 pause 后的完整内容。
]

支持 *粗体强调*、_斜体标记_ 和 `行内代码`，也可以使用 #red[标红]、#bred[粗体标红]、#yellow[标黄]、#byellow[粗体标黄] 的写法。

#pause

#v(0.3em)

列表示例：

- 无序列表第一项
- 无序列表第二项
  - 嵌套子项 A
  - 嵌套子项 B
    - 三级嵌套
    - 三级嵌套
- 无序列表第三项

#v(0.3em)

+ 有序列表第一项
+ 有序列表第二项
+ 有序列表第三项

== Textbox 组件

`textbox` 接受多个 content，自动等分为等高文本框列：

#v(0.5em)

#textbox(
  [*左侧*

  这里放置第一列的内容，可以包含任意长度的文本段落],
  [*中间*

  第二列的内容会自动与其他列等高对齐],
  [*右侧*

  第三列同理，列数不限于三列],
)

#v(0.5em)

两列文本框：

#textbox(
  [*第一列*

  两列布局适合左右对比的内容展示],
  [*第二列*

  每列底部会被 `lazy-v(1fr)` 自动撑齐],
)

// ═══════════════════════════════════════════
= 数据展示

== 表格样式

默认表格带有 `sea` 色表头和斑马纹行底色：

#v(0.3em)

#figure(
  table(
    columns: (auto, 1fr, auto, auto),
    [编号], [名称], [类型], [状态],
    table.hline(),
    [001], [苹果], [水果], [正常],
    [002], [胡萝卜], [蔬菜], [正常],
    [003], [牛奶], [饮品], [缺货],
    [004], [面包], [烘焙], [正常],
    table.hline(),
  ),
  caption: [商品库存示例表格，表头自动应用白色加粗 + `sea` 底色],
)

== 代码块与数学公式

行内代码 `let x = 42` 使用 `skyll` 底色圆角样式。

#v(0.3em)

代码块示例：

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

#v(0.5em)

数学公式（带编号）：

#set math.equation(numbering: "(1)")

$ integral_0^infinity e^(-x^2) dif x = sqrt(pi) / 2 $

$ sum_(k=0)^n binom(n, k) x^k y^(n-k) = (x + y)^n $

== 图片与 Figure

#figure(
  rect(width: 60%, height: 6em, fill: gradient.linear(rgb("#3b60a0"), rgb("#bdd0f1")), radius: 0.5em),
  caption: [渐变色占位图，实际使用时替换为 `image("path.png")`],
)

#v(0.5em)

图片和表格都通过 `figure` 包裹后自动获得编号与 caption，表格 caption 在顶部，图片 caption 在底部。

// ═══════════════════════════════════════════
= 页面版式

== Grid 与混合布局

使用 `grid` 实现左右分栏：

#grid(
  columns: (1fr, 1fr),
  gutter: 0.8em,
  [
    #textbox(
      [*左栏*

      - 项目甲
      - 项目乙
      - 项目丙],
    )

    #v(0.6em)

    #textbox(
      [*补充说明*

      左栏可以堆叠多个 textbox 组件],
    )
  ],
  [
    #v(0.3em)

    右栏可以放置段落文字、图片或其他任意内容。

    #v(0.3em)

    这种左右分栏布局适合图文对照、数据与说明并排等场景。
  ],
)

== Textbox 与表格组合

#textbox(
  [*分类一*

  可以在 textbox 内部嵌入简短的要点说明

  #v(0.3em)
  - 要点 A
  - 要点 B
  - 要点 C],

  [*分类二*

  也可以放入编号列表或其他结构

  #v(0.3em)
  + 步骤一
  + 步骤二
  + 步骤三],
)

#v(0.5em)

#table(
  columns: (auto, auto, auto, auto, auto),
  [指标], [方案 A], [方案 B], [方案 C], [方案 D],
  table.hline(),
  [速度], [快], [中], [慢], [快],
  [成本], [高], [低], [中], [低],
  [质量], [优], [良], [优], [中],
  table.hline(),
)

// ═══════════════════════════════════════════
= 特殊页面

== 箭头与 physica 符号

#grid(
  columns: (1fr, 1fr),
  gutter: 0.8em,
  [
    主题内置 ASCII 箭头自动替换：

    #v(0.2em)

    - `->` 右箭头：a -> b
    - `-->` 长右箭头：a --> b
    - `=>` 双线箭头：a => b
    - `==>` 长双线箭头：a ==> b
    - `|->` 映射箭头：f |-> g
  ],
  [
    physica 包提供数学简写：

    #v(0.2em)

    $ A^T $ （转置 `super-T-as-transpose`）

    $ integral f(x) dif x $ （微分符号 `dif`）

    $ pdv(f, x) quad pdv(f, x, 2) $ （偏导 `pdv`）
  ],
)

== Info 组件与链接 <touying:hidden>

`info` 用于左右两端对齐的信息行，适合简历、项目概览等场景：

#v(0.4em)

#info[项目名称][xwysyy-typst]
#info[技术栈][Typst + touying 0.7.3]
#info[字体][Libertinus Sans + LXGW WenKai]
#info[许可证][MIT]

#v(0.5em)

链接自动显示为 `sea` 色下划线，*粗体*与 `行内代码` 可混排，行内公式 $E = m c^2$ 正常渲染。

#focus-slide[
  Focus Slide

  深色全屏 · 居中大字
]

#image-slide(
  body: [Image Slide：全屏背景图 + 底部半透明标题条],
  img: rect(width: 100%, height: 100%, fill: gradient.linear(sea, sky, angle: 135deg)),
)

#end-slide(
  title: [谢谢！],
  body: [xwysyy theme demo],
)
