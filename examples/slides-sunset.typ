#import "../xwysyy.typ": *

#show: xwysyy-pre.with(
  theme: "sunset",
  config-info(
    title: [xwysyy 主题功能演示],
    subtitle: [Sunset 配色方案 · 组件速览],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()

#outline-slide()

// ═══════════════════════════════════════════
= 基础排版

== 文本与强调

这是一段普通正文，用于展示#red[默认字体、字号与行距的效果]。

#v(0.5em)

支持 *粗体强调*、_斜体标记_ 和 `行内代码`，也可以使用 #red[标红]、#bred[粗体标红]、#yellow[标黄]、#byellow[粗体标黄] 的写法。

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

`textbox` 是轻量文本框，浅色背景圆角矩形：

#v(0.3em)

#textbox[单个文本框：适合放置备注、引用或补充说明内容。]

#v(0.3em)

多列等高文本框：

#textbox(
  [*左侧*

  这里放置第一列的内容，可以包含任意长度的文本段落],
  [*中间*

  第二列的内容会自动与其他列等高对齐],
  [*右侧*

  每列底部会被 `lazy-v(1fr)` 自动撑齐],
)

// ═══════════════════════════════════════════
= 数据展示

== 表格样式

默认表格带有主题色表头和斑马纹行底色：

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
  caption: [商品库存示例表格，表头自动应用白色加粗 + 主题色底色],
)

== 代码块与数学公式

行内代码 `let x = 42` 使用主题浅色底圆角样式。

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

// ═══════════════════════════════════════════
= 页面版式

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

#focus-slide[
  Focus Slide

  深色全屏 · 居中大字
]

#end-slide(
  title: [谢谢！],
  body: [sunset theme demo],
)
