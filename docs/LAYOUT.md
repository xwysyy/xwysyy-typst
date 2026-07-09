# 语义布局层与版面遥测

## 要解决的问题

AI 生成幻灯片时，间距处理不稳定：内容常挤在页面上方留下大片底部空白，或者图片和说明文字被过大的间隙拆开。根因不是模型没有审美，而是它在编译后拿不到足够细的版面数据。模型看到的是源码或一张整体截图，无法稳定知道某个块渲染后的真实高度、两块之间的归一化间距、底部空白占了多少、视觉重心偏到哪里。于是它只能靠手写 `v(6em)` 猜间距，而"适中""不要太空"这类词无法稳定映射成数值。

这一层不做全自动排版器（那样风格会收敛、难以表达意图），而是把版面变成可测量、可比较、可调参的数值：作者选一个语义组件、填内容、给角色和 mode，组件负责测量真实高度、按节奏分配留白、导出归一化几何；Python checker 读这些几何给出内容级诊断；AI 据数值反馈调整，而不是猜坐标。

## 三个部件

组件层 `src/layout.typ` 提供八个语义版式（`duo` / `focus` / `grid` / `stack` / `compare` / `stat` / `figure` / `sidebar`），每个都在编译期 `measure` 每个块的真实高度，按填满优先分配留白，并把测量出的归一化 bbox 导出为 `<xwysyy-slide-layout>` metadata。

checker `scripts/slide-check.py` 读 `typst query` 的输出，计算密度、重心、留白、语义关系间距，报告作者需要决策的内容级问题。它不修间距（间距由组件保证），只判断内容太少、太多、列失衡、语义对被拆开、溢出这些组件无法自行决定的事。

契约见本文末尾，写进了 `AGENTS.md`，约束 AI 只用组件、不手写间距坐标、编译后读 checker 数值再调。

## 填满优先（fill-first）

组件默认让主体内容占满版心，而不是把内容当一个小组居中、剩余空间变成大片外边距（那样看着稀疏、半空）。外边距钉小且固定（上 7%、下 9%），多出来的空间用于放大内容：图撑成主体、卡片做高做实。图文对里图占据 takeaway 之上的全部空间、takeaway 钉在底部；多列（`grid`/`compare`/`stat`/`sidebar`）的卡片至少占版心 60% 高、内容在卡内垂直居中。内容真的超过版心时才触发 `content_overflow`。放真实图片时用 `image(width: 100%)`，占位测试用 `rect(height: 100%)` 填满分配到的图区。

## 组件 API

坐标一律相对当前 slide body（页头页脚之内的正文区）归一化到 `[0, 1]`。作者不写坐标，坐标由组件测量后自动导出。

### duo-slide

一个上下语义对，例如上图下结论。

```typst
#duo-slide(
  title: [核心发现],
  top: image("overview.png", width: 100%),
  bottom: textbox[*结论。* 该方法在保持可解释性的同时降低了推理成本。],
  top-role: "main_visual",
  bottom-role: "takeaway",
  mode: "balanced",
)
```

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| `top` / `bottom` | none | 上块 / 下块内容 |
| `mode` | `"balanced"` | `compact` / `balanced` / `separated`，控制两块间距密度 |
| `top-role` / `bottom-role` | `figure` / `explanation` | 角色，影响视觉权重估算 |
| `relation` | `"supports"` | 语义关系标签（`caption` / `supports` / `contrast` / `independent`） |
| `top-width` / `bottom-width` | 0.82 / 0.74 | 归一化宽度 |

### focus-slide

内容少时的单焦点居中页。

```typst
#focus-slide(
  title: [一句话结论],
  body: textbox[*主要结论。* 本页只讲一件事。],
  width: 0.76,
)
```

### grid-slide

N 个等高对等列。每列画成等高的主题卡片（可见卡片等高，不只是隐形外框），列高自动取最大，垂直居中。传纯内容即可，组件负责画卡；`card: false` 用于图片等不需要卡片背景的内容。

```typst
#grid-slide(
  title: [三步流程],
  columns: ([*测量。* 编译期测真高], [*反馈。* 导出归一化几何], [*决策。* agent 读数值]),
  roles: ("column", "column", "column"),
  gutter: 0.04,
)
```

### stack-slide

N 个竖直块按同一节奏均分，等于 duo 的多块推广。

```typst
#stack-slide(
  title: [概览与要点],
  blocks: (image("fig.png"), textbox[要点一], textbox[要点二]),
  roles: ("main_visual", "explanation", "explanation"),
  mode: "balanced",
)
```

### compare-slide

左右两张等高卡片，读作一组对比，导出水平关系和高度差。同样传纯内容，组件画等高卡片（`card: false` 关闭卡片背景）。

```typst
#compare-slide(
  title: [两种方案],
  left: [*方案 A。* 风格收敛，难表达意图。],
  right: [*方案 B。* 组件保证间距，agent 调内容。],
  gutter: 0.06,
)
```

### stat-slide

一行指标卡片，每张一个大数字加标签。复用 grid 的等高卡片行，只负责数字/标签排版。

```typst
#stat-slide(title: [关键指标], stats: (
  (value: [38%], label: [成本下降]),
  (value: [0.4], label: [精度损失]),
  (value: [6], label: [数据集]),
))
```

### figure-slide

图 + 紧贴 caption + 可选 takeaway。图和 caption 结成紧密组，组与 takeaway 是支持关系。复用 focus / duo。

```typst
#figure-slide(
  title: [主结果],
  fig: image("overview.png"),
  caption: [图 1. 精度不变而成本下降。],
  takeaway: textbox[*结论。* 在保持可解释性的同时降低推理成本。],
)
```

### sidebar-slide

窄标签条（主题深色）加宽内容卡片，非对称双栏，两栏等高。

```typst
#sidebar-slide(
  title: [方法概览],
  label: [方法],
  body: textbox[编译期测真高，按节奏分配留白，导出遥测。],
  label-width: 0.26,
)
```

每个组件都接受 `debug: true`，在页面上叠加测量出的 bbox 矩形和 id，方便人工核对 checker 看到的和渲染的是否一致。

### 双产物降级

所有组件在 `--input mode=note`（即 `xwysyy-doc` 的笔记产物）下自动退化为线性内容：duo 变成上块接下块，grid / compare 变成并排文本框，stack 变成堆叠块，不输出绝对坐标。slide 产物和 note 产物共用同一份源码。

## 遥测 schema

每页导出一条带 `<xwysyy-slide-layout>` label 的 metadata：

```json
{
  "schema": "xwysyy-slide-layout/v1",
  "id": "good-duo",
  "archetype": "duo",
  "coordinate_system": "normalized-slide-body",
  "objects": [
    { "id": "good-duo:top", "role": "main_visual", "group": "good-duo",
      "x": 0.09, "y": 0.19, "w": 0.82, "h": 0.29 }
  ],
  "relations": [
    { "from": "good-duo:top", "to": "good-duo:bottom",
      "kind": "supports", "axis": "vertical", "desired_proximity": "medium" }
  ],
  "extra": { "mode": "balanced", "gap_ratio": 0.13, "free_ratio": 0.47, "overflow": false }
}
```

`objects[*]` 的 `x/y/w/h` 是组件 `measure` 后的真实渲染几何，不是作者声称的数字。这是它和一次性把手写坐标原样吐回的做法的关键区别：checker 看到的就是页面上真实发生的。

## checker 诊断

```bash
typst compile --root . examples/layout-demo.typ /tmp/demo.pdf
typst query --root . examples/layout-demo.typ '<xwysyy-slide-layout>' --field value > /tmp/layout.json
scripts/slide-check.py /tmp/layout.json --format text
# 或一条龙：
scripts/slide-telemetry examples/layout-demo.typ
```

| 诊断 | 级别 | 触发条件 |
| --- | --- | --- |
| `content_overflow` | error | 组件报告内容高于 body，被迫压掉外边距 |
| `semantic_pair_split` | error | 语义对间距超出其 proximity 上界 |
| `low_density` | warning | ink 覆盖低于该 archetype 的下限 |
| `over_dense` | warning | ink 覆盖高于 0.80（`grid`/`compare`/`sidebar` 因等高卡片天然铺满，排除在外） |
| `content_clustered_top` / `_bottom` | warning | 加权重心偏离且对应方向留白过大 |
| `column_imbalance` | warning | grid / compare 列的自然高度差超过 0.35 |
| `crowded_related_pair` | warning | 语义对间距低于 proximity 下界 |
| `wide_gutter` | warning | 并排列的水平 gutter 过宽（水平关系专用，不当作语义对拆裂） |
| `weak_relation_alignment` | warning | 垂直语义对水平中心偏差超过 0.10 |
| `trapped_whitespace` | warning | 两个无声明关系的竖直相邻块之间垂直间隙超过 0.30（组件都声明关系，此项只对手写遥测生效） |
| `object_outside_body` | error | bbox 越出 `[0, 1]`；已报 `content_overflow` 的页不再重复报此项 |

checker 还会对损坏的输入报结构性诊断：`invalid_object`、`invalid_bbox`、`negative_size`（error）与 `empty_slide`、`missing_relation_target`（warning）。这些针对手写或损坏的遥测，正常组件产出不会触发。

密度下限按 archetype 区分，因为 focus 页天生稀疏、grid 页列等高后偏矮：focus 0.08，grid / compare 0.12，duo / stack 0.15。这些是启发式初值，不是审美真理，可用 `--rules rules.json` 覆盖，长期应按每个 deck 的历史优秀页统计分布重新校准。

对称的外部留白（居中的组围绕上下留白）不算缺陷，永远不报；只有非对称留白、语义对内部裂隙、密度失衡、列失衡才报。

## AI 调参循环

```bash
typst compile --root . deck.typ deck.pdf
typst query --root . deck.typ '<xwysyy-slide-layout>' --field value > layout.json
scripts/slide-check.py layout.json --format json
```

拿到诊断后：`content_overflow` 先拆页或删字；`low_density` 放大主视觉、补说明或并页；`column_imbalance` 把长列单独成页；`semantic_pair_split` 收紧 mode；`content_clustered_*` 一般不该出现（组件已居中），出现说明用了手写坐标，改回组件。调完重新编译、查询、检查，直到无 error，warning 由人工判断。

## 生成契约

禁止：手写 `#v(...)` 制造大间距；用绝对坐标或 `place` 控制普通正文；用 `align(bottom)` 把正文推到底部；在一页里堆多个无约束 block。

必须：图文上下结构用 `duo-slide`；单一结论少内容用 `focus-slide`；多列对等信息用 `grid-slide`；多块同节奏用 `stack-slide`；左右对比用 `compare-slide`；一行关键数字用 `stat-slide`；图配 caption 与结论用 `figure-slide`；窄标签配宽内容用 `sidebar-slide`；只通过 `mode: compact | balanced | separated` 调密度；编译后跑 checker，按返回的数值修正，不靠"看起来差不多"停止迭代。
