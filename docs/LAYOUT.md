# 语义布局层与版面遥测（schema v4）

## 要解决的问题

AI 生成幻灯片时，间距处理不稳定：内容常挤在页面上方留下大片底部空白，或者图片和说明文字被过大的间隙拆开。根因不是模型没有审美，而是它在编译后拿不到足够细的版面数据。模型看到的是源码或一张整体截图，无法稳定知道某个块渲染后的真实高度、两块之间的归一化间距、底部空白占了多少、视觉重心偏到哪里。于是它只能靠手写 `v(6em)` 猜间距，而"适中""不要太空"这类词无法稳定映射成数值。

这一层不做全自动排版器（那样风格会收敛、难以表达意图），而是把版面变成可测量、可比较、可核对的数值：作者选一个语义组件、填 typed item，组件负责测量真实尺寸、按声明的 sizing 分配空间、导出归一化几何；checker 读这些几何给出内容级诊断；像素层把真实渲染和遥测交叉对账。AI 据数值反馈调整，而不是猜坐标。

schema v4 在 v3 的测量诚实之上，把**信任边界**收紧成五条原则：

1. **sizing 是声明的，不是猜的**。要填满槽位的内容必须写成 `visual(...)`（fit 默认 `"stretch"`）；必填槽位传 `none` 直接 panic；文本槽（card / takeaway / plain / metric 字段）的内容必须有可测量的宽和高——纯 spacer、空字符串、裸线条都在编译期 panic，而不是被扩成一块假 payload。
2. **声明的 payload 是主张，不是证据**。stretch 槽位和百分比宽度媒体的 payload 标记为 `payload_source: "declared"`，不计入密度与空壳判定；它的证据来自像素层的逐对象墨迹检查（agent profile 强制渲染像素）。
3. **身份是稳定的**。自动 slide id 绑 touying 的逻辑页计数器（不绑物理页码），reveal 的每一帧都能联结回它的 layout record；孤儿帧、缺步、帧数不符、重复 id 都是结构 error，coverage 只认联结成功的帧。
4. **对象带四个框加来源**。`frame`（分配到的容器）、`preferred`（分配器看到的自然外框）、`payload`（内容真实的二维 flow bbox）、`paint`（可见卡片色块 + 填色 `paint_fill`）；不可折行的超宽内容导出 `overflow_x` 证据。
5. **解析 fail-closed**。缺字段、未知枚举、非有限数、负尺寸、旧版 schema 一律以输入错误退出（exit 2），不做默认值兜底；fit 四态各自带数值不变量，自相矛盾的状态是 error。

## 四个部件

组件层 `src/layout.typ` 提供八个语义版式（`duo` / `focus` / `grid` / `stack` / `compare` / `stat` / `figure` / `sidebar`），共用一个分配器，导出 `<xwysyy-slide-layout>` v4 metadata。每个 slide 版式（含标题页、章节页等）另导出一条 `<xwysyy-page>` 页面清单；每个实际渲染的 subslide 导出一条 `<xwysyy-frame>` v2 映射（含该页版心的物理几何）；内容页页头导出 `<xwysyy-header>` v2（标题缩放比例与横向、纵向是否放得下）。

checker `scripts/slide-check.py` 读 `typst query` 的输出（按 `schema` 字段识别，任意混合输入均可），先做结构校验（帧状态机、fit 不变量、越界与逃逸），再计算密度、重心、留白、语义关系间距与遥测覆盖率，报告作者需要决策的内容级问题。它不修间距（间距由组件保证），只判断内容太少、太多、空壳卡片、列失衡、语义对被拆开、溢出、漏遥测这些组件无法自行决定的事。每条诊断带机器可执行的 `action` 标签，级别由统一的政策表决定。

统一 CLI `scripts/xwysyy-check` 一条命令跑完整个闭环：一次 `typst query "metadata"` 同时拿到全部四种 schema，跑几何检查；`--pixels` 时再渲染 PNG 做像素交叉验证。**`--profile agent` 强制启用像素**：几何层对 declared payload 明确不背书，不渲染就无法闭环。`scripts/slide-check.py` 保留为可独立调用的几何引擎（输入是现成的 JSON 时用它）。

```bash
scripts/xwysyy-check deck.typ                 # 几何检查（human profile）
scripts/xwysyy-check deck.typ --profile agent # 几何 + 像素 + agent 契约（像素强制）
```

生成契约见本文末尾，写进了 `AGENTS.md`，约束 AI 只用组件、不手写间距坐标、不碰 `tuning`、编译后读 checker 数值再调。

## 填满优先（fill-first）与 fit 四态

组件默认让主体内容占满版心，而不是把内容当一个小组居中、剩余空间变成大片外边距。外边距钉小且固定（上 7%、下 9%，安全区 0.84H），富余空间分给可生长的块：stretch 视觉撑成主体、卡片做高做实。多列（`grid`/`compare`/`stat`/`sidebar`)的卡片至少占版心 60% 高；`stack` 里 stretch 视觉吸收全部富余，纯文本堆叠则所有卡片均摊做高。没有可生长块时（例如自然尺寸的图配短说明），组件把整组在安全区内居中，遥测如实报告低密度，而不是把透明框撑大伪装成满。唯一例外是 `focus`：单点定格页保留对称居中留白，但安全区规则照常适用。

分配器按 item 五元组（min / preferred / max / grow）与 gap 二元组（min / preferred）解算，报告四态之一，每态带 checker 强制的数值不变量：

| 状态 | 含义 | 不变量 | checker 反应 |
| --- | --- | --- | --- |
| `normal` | preferred 全放进安全区，富余按 grow 分配（max 封顶后水位重分） | `gap_ratio == 1`，零 deficit / overflow | 无 |
| `compressed` | 语义间隙压到 preferred 之下（不低于 min，即 0.4 倍）才放进安全区 | `gap_ratio < 1`，零 deficit / overflow | `gap_compressed` warning |
| `tight` | 只有吃掉外边距才放得下（间隙已在 min） | `margin_deficit_ratio > 0`，零 overflow | `margin_squeeze` error |
| `overflow` | 全部取最小值仍超出整页 | `body_overflow_ratio > 0` | `content_overflow` error |

`gap_ratio` 是实际间隙与 preferred 间隙的真实比值（无间隙的版式恒为 1），不是插值参数。违反不变量（例如报 normal 却带正的 overflow）是 `invalid_fit_state` error：导出器坏了或遥测被伪造。stretch 视觉带 0.28H 的硬下限：文字多到把视觉挤到下限之下时，页面如实降级为 tight / overflow，而不是把主视觉饿死到 0.01H 还报 normal。行版式（grid / compare / stat / sidebar）没有可压缩间隙，只有 normal / tight / overflow 三态。

## typed items 与声明式 sizing

所有组件槽位接受 typed item；纯内容按组件语义自动包装（见各组件说明）：

```typst
visual(body, fit: "stretch")   // 视觉块：不画卡片。stretch = 填满分配到的槽
visual(body, fit: "natural")   // 固有尺寸的视觉（image(width: 100%) 之类）
card(body, role: "explanation") // 主题卡片
takeaway(body)                  // 结论卡片（role 固定 takeaway）
plain(body, role: "text")       // 不画卡片的文本块
metric(value, label)            // stat-slide 的指标条目
```

`role` 是封闭集合（`main_visual` / `figure` / `explanation` / `takeaway` / `text` / `caption` 等，见 `_ROLES`），只影响视觉重心的权重估算，改变不了 checker 的控制流——没有 `decorative` 之类把对象从检查里摘出去的逃生门，未知 role 在编译期 panic。

stretch 视觉的正确填法：占位图 `rect(width: 100%, height: 100%)`，真实图片 `image("f.png", width: 100%, height: 100%, fit: "contain")`。natural 视觉用 `image("f.png", width: 100%)`。百分比尺寸的内容**必须**包 `visual(...)`：文本槽收到测量宽度为零的内容（percent 宽媒体和 spacer 的测量签名相同）直接 panic，只有 visual 槽允许以槽宽登记 payload，且标记为 `declared`、由像素层验证。

校验都发生在编译期，失败即 panic：必填槽位为 `none`；visual 内容完全渲染为空；文本槽内容无可测量宽度（spacer、空字符串）或无可测量高度（裸线条）；`grid` 少于 2 列（单块用 `stack` 或 `focus`）；`grid` / `compare` 列里放 `visual(fit: "stretch")`（行版式按自然高度排版）；`figure` 的 takeaway 槽放 stretch visual；`stat` 的条目不是 `metric(...)` 或 value / label 渲染为空；`focus` / `sidebar` 收到 `reveal-from`（它们没有展示步骤）；`sidebar` 槽位收到 typed item（它自己画卡片）；`reveal-from` 不是 `[1, 步数]` 内的整数；`tuning` 的 key 拼错、类型不对或超出允许区间；`visual` 的 `fit` 不是 `"stretch"` / `"natural"`；role 不在封闭集合内；`xwysyy-slide` 收到 `kind` 参数（豁免页只能由 `outline-slide` / `title-slide` 等自己的版式产生）；`image-slide` 没有传图。这些校验在 slides 与 note 两种产物下一致执行（note 模式用名义宽度做同样的空内容断言）。

已知边界：槽位内容里的 `place(...)` 脱离文档流，几何遥测测不到它；`hide(...)` 保留完整布局尺寸，几何层也看不出来——两者都由像素层兜底（stray ink 与逐对象 hollow 检查）。

## 分步展示（reveal）与 `#pause` 禁令

touying 的 `#pause` / 全局 `#uncover` 依赖 markup 里的 marks，进不了组件内部的 `context` / `layout` 闭包，放进组件内容里 touying 会直接 panic。带展示顺序的组件因此提供 `reveal: true`：块按语义顺序逐个 subslide 浮现。所有组件走同一个 resolver：**显式 `reveal-from` 恒优先于 `reveal: true` 的语法糖**（糖只作用于没写 `reveal-from` 的 item）。`duo` / `compare` 的第二块默认第 2 步出现，`stack` / `grid` 的第 i 块默认第 i 步出现，`figure` 的图默认第 1 步、takeaway 默认第 2 步（caption 始终跟随图）；`stat` 的 `metric(...)` 也接受 `reveal-from`。不支持展示步骤的组件（`focus` / `sidebar`）收到 `reveal-from` 会 panic，而不是静默忽略。隐藏步骤保留测量空间，所以每个 subslide 的版面完全一致。

每个实际渲染的 subslide 发一条 `<xwysyy-frame>` v2 映射（id、step、steps、物理页码、是否 handout、版心物理几何）；完整遥测记录在末帧导出一次，对象带 `visible_from`。自动 id 来自 touying 的逻辑页计数器（`"<archetype>@s<n>"`），跨 subslide 与 handout 稳定，所以每一帧都联结得回 record。checker 校验帧状态机（正常输出恰好是连续物理页上的 1..N 步；handout 只有末帧一条）并重建每个真实渲染帧：逐帧查重叠、空帧（某一步什么都不显示是 error）、稀疏帧（早期帧几乎没有内容是 `sparse_frame`，agent 下 error）。需要更复杂动画的页面不要用布局组件，退回手写 `xwysyy-slide` 加 `#pause`。

```typst
#duo-slide(title: [主结果], top: visual(image("fig.png", width: 100%, height: 100%, fit: "contain")),
  bottom: [*结论。* 第二步才浮现，版面不动。], reveal: true)
```

## 组件 API

坐标一律相对当前 slide body（页头页脚之内的正文区）归一化到 `[0, 1]`。作者不写坐标，坐标由组件测量后自动导出。`id: auto` 自动展开成 `"<archetype>@s<逻辑页号>"`（跨 reveal 子页稳定）；同类多页建议仍显式命名。数字微调参数全部收在 `tuning` 字典里（key、类型、区间均校验，违规 panic）；AI 生成契约禁改 `tuning`，遥测的 `extra.tuned` 记录是否用过，agent profile 下用了就是 error。

每个组件都接受 `debug: true`：实线画分配框（frame）、虚线画 payload 框，方便人工核对 checker 看到的和渲染的是否一致。

### duo-slide

一个上下语义对，例如上图下结论。`top` 的纯内容按 `visual(fit: "natural")` 包装（要撑满就显式写 `visual(...)`），`bottom` 的纯内容按 `card()` 包装。

```typst
#duo-slide(
  title: [核心发现],
  top: visual(image("overview.png", width: 100%, height: 100%, fit: "contain")),
  bottom: card([*结论。* 该方法在保持可解释性的同时降低了推理成本。], role: "takeaway"),
  mode: "balanced",
)
```

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| `top` / `bottom` | 必填 | 上块 / 下块（typed item 或纯内容） |
| `mode` | `"balanced"` | `compact` / `balanced` / `separated`，控制两块间距密度 |
| `relation` | `"supports"` | 语义关系标签，封闭集合 `supports` / `contrast` |
| `reveal` | `false` | 为 `true` 时 bottom 在第 2 个 subslide 浮现（`reveal-from` 可覆盖） |
| `tuning` | `(:)` | `top-width`（0.82）、`bottom-width`（0.74），区间 [0.3, 0.95] |

### focus-slide

内容少时的单焦点居中页，纯内容按 `card()` 包装。填满优先的唯一例外：定格页保留对称居中留白，遥测带 `intent: "focus"`，密度由 checker 的 `low_density` 把关；内容超出安全区照样报 tight / overflow。单帧组件：`reveal-from` 与 stretch visual 都会 panic。`tuning`：`width`（0.76，[0.3, 0.95]）、`center-y`（0.46，[0.30, 0.70]）。

```typst
#focus-slide(title: [一句话结论], body: [*主要结论。* 本页只讲一件事。])
```

### stack-slide

N 个竖直块，duo 的多块推广。纯内容按 `card()` 包装。

```typst
#stack-slide(
  title: [概览与要点],
  items: (
    visual(rect(width: 100%, height: 100%, fill: aqua)),
    card([*要点一。* 编译期测真高。]),
    takeaway([*结论。* 富余进卡内不进间隙。]),
  ),
)
```

stretch 视觉吸收全部富余；没有 stretch 视觉时所有 `card` 均摊富余一起做高（`takeaway` / `plain` / natural 视觉保持自然高度）。块间距离由 `mode` 决定。每个 item 可传 `reveal-from: <n>`（默认 `reveal: true` 时第 i 块第 i 步）。`items` 为空 panic。`tuning`：`width`（0.82，[0.3, 0.95]）。

### grid-slide

N 个等高对等列（N ≥ 2，单块请用 stack / focus）。纯内容按 `card()` 包装成等高主题卡片，列高取最大自然高（至少 0.6H）。相邻列带 `peer` 关系，checker 校验 gutter。`reveal: true` 时第 i 列从第 i 个 subslide 浮现。行版式按自然高度排版，列里不接受 `visual(fit: "stretch")`（在 note / slides 两种产物下都 panic）。`tuning`：`gutter`（0.04，[0, 0.2]）。

```typst
#grid-slide(
  title: [三步流程],
  columns: ([*测量。* 编译期测真高], [*反馈。* 导出归一化几何], [*决策。* agent 读数值]),
)
```

### compare-slide

左右两张等高卡片（都必填），读作一组对比，内容顶部对齐（两侧开头落在同一行，对比才可读）。纯内容按 `card()` 包装；stretch visual panic。`reveal: true` 时右侧在第 2 个 subslide 浮现（`reveal-from` 可覆盖）。`tuning`：`gutter`（0.06，[0, 0.2]）。

```typst
#compare-slide(
  title: [两种方案],
  left: [*方案 A。* 风格收敛，难表达意图。],
  right: [*方案 B。* 组件保证间距，agent 调内容。],
)
```

### stat-slide

一行指标卡片，每张一个大数字加标签，独立行引擎。条目必须用 `metric(value, label, reveal-from: auto)` 构造，value / label 渲染为空 panic。payload 分别测量 value 与标签的真实宽度（不再测被强制成整行宽的外壳）。过长的 value 自动缩小到贴合卡片宽度（下限 0.6 倍，低于下限就折行、卡片变高、由 fit 如实报告），实际缩放比例导出在 `extra.value_scales`。`reveal: true` 时第 i 张第 i 步浮现。`tuning`：`gutter`（0.04，[0, 0.2]）。

```typst
#stat-slide(title: [关键指标], stats: (
  metric([38%], [成本下降]),
  metric([0.4], [精度损失]),
  metric([6], [数据集]),
))
```

### figure-slide

图 + 紧贴 caption + 可选 takeaway。先测 caption 再给图槽显式高度，所以 stretch 图安全地填满图槽（Typst 的 `measure` 对无界上下文里的百分比高度返回 0，直接组合会让内容逃出外框）。`fig` 的纯内容按 `visual(fit: "natural")` 包装，要撑满写 `visual(...)`；`takeaway` 的纯内容按 `takeaway()` 包装，stretch visual panic。caption 间隙固定 0.5em 不参与压缩。reveal 走统一 resolver：`reveal: true` 时图第 1 步、takeaway 第 2 步（各自的 `reveal-from` 可覆盖，caption 跟随图）。`tuning`：`figure-width`（0.80）、`takeaway-width`（0.74），区间 [0.3, 0.95]。

```typst
#figure-slide(
  title: [主结果],
  fig: visual(image("overview.png", width: 100%, height: 100%, fit: "contain")),
  caption: [图 1. 精度不变而成本下降。],
  takeaway: [*结论。* 在保持可解释性的同时降低推理成本。],
)
```

### sidebar-slide

窄标签条（主题深色）加宽内容卡片，非对称双栏，两栏等高。`label` 和 `body` 都必填、传纯内容（组件自己画卡片：typed item 会 panic，`textbox` 会双层卡片）。没有 `reveal`（标签和内容没有展示先后）。`tuning`：`label-width`（0.26，[0.1, 0.5]）、`gutter`（0.04，[0, 0.2]）。

```typst
#sidebar-slide(
  title: [方法概览],
  label: [方法],
  body: [编译期测真高，按节奏分配留白，导出遥测。],
)
```

### 双产物降级

所有组件在 `--input mode=note`（即 `xwysyy-doc` 的笔记产物）下自动退化为线性内容：duo 变成上块接下块，grid / compare 变成并排文本框，stack 变成堆叠块，reveal 折叠为完整内容，不输出绝对坐标。槽位校验（typed item 合法性、tuning、空内容断言）在两种产物下一致执行：note 编译得过而 slides 编译崩的源文件不存在。

## 遥测 schema v4

每页导出一条带 `<xwysyy-slide-layout>` label 的 metadata：

```json
{
  "schema": "xwysyy-slide-layout/v4",
  "id": "good-duo",
  "archetype": "duo",
  "layout_engine": "column",
  "page": 4,
  "frame_count": 1,
  "coordinate_system": "normalized-slide-body",
  "objects": [
    { "id": "good-duo:top", "object_kind": "visual", "semantic_role": "main_visual",
      "group": "good-duo",
      "frame":     { "x": 0.09, "y": 0.07, "w": 0.82, "h": 0.607 },
      "preferred": { "w": 0.82, "h": 0.28 },
      "payload":   { "x": 0.09, "y": 0.07, "w": 0.82, "h": 0.607 },
      "paint": null,
      "paint_fill": null,
      "payload_source": "declared",
      "overflow_x": false,
      "sizing": { "x": "stretch", "y": "stretch" },
      "visible_from": 1 }
  ],
  "relations": [
    { "from": "good-duo:top", "to": "good-duo:bottom",
      "kind": "supports", "axis": "vertical", "desired_proximity": "medium" }
  ],
  "fit": { "state": "normal", "required_height_ratio": 0.51, "gap_ratio": 1.0,
           "margin_deficit_ratio": 0, "body_overflow_ratio": 0 },
  "extra": { "mode": "balanced", "gap_fraction": 0.13, "tuned": false }
}
```

四个框的分工：`frame` 是组件分配的容器；`preferred` 是分配器看到的自然外框（审计分配决策用）；`payload` 是内容真实的二维 flow bbox（含横向：一张窄图的 payload 宽度是图宽，不再抄 frame 宽度；对折行文本是近似框，不是字形墨水）；`paint` 是可见卡片的色块，`paint_fill` 是它的填色（像素层用来区分"卡片背景"和"卡片内容"的墨迹）。`payload_source` 区分测量值与声明值：`declared`（stretch 槽、percent 宽媒体）不计入密度与空壳判定，由像素层验证。`overflow_x` 是不可折行内容超出槽宽的证据（可折行文本被诚实钳制，不误报）。payload 高度不截断到 frame 内，溢出的内容会把 payload 探出框外，checker 看得见；payload 横向探出自身 frame、或在 normal / compressed 状态下纵向探出，都是 `object_escapes_frame` error。

`object_kind`（`visual` / `card` / `takeaway` / `plain`）与 `semantic_role` 都是封闭集，未知值是解析错误（exit 2），不是告警。`archetype` 是语义类型，`layout_engine` 是底层引擎（`column` / `row` / `single`）。

配套的三种记录：`<xwysyy-page>`（`{"kind": "content|title|section|end|image|outline", "page": n}`，豁免 kind 只能由对应版式函数产生；同一物理页出现两条清单是 error）；`<xwysyy-frame>` v2（每个实际渲染 subslide 一条：`id` / `step` / `steps` / `page` / `handout`，外加 `body` 与 `page_size` 的物理 pt 几何，像素层据此换算坐标，不再硬编码模板常量）；`<xwysyy-header>` v2（每个内容页一条：标题缩放 `scale`、横向 `fits`、标题实际高度 `height` 与纵向 `fits_v`——显式换行或超高标题会撞页头带，报 error）。

## checker 诊断

```bash
scripts/xwysyy-check deck.typ                          # 一次 query，全部 schema
scripts/xwysyy-check deck.typ --input handout=true --format json
scripts/slide-check.py merged.json --page-count 21     # 已有 JSON 时的几何引擎
```

覆盖指标全部用矩形并集：`container_coverage`（frame 并集）、`visual_coverage`（paint + payload 并集，眼睛看到的墨水）、`payload_density`（**measured** payload 并集，真实内容）、`declared_payload`（声明 payload 并集，供参考）、`payload_utilization`（payload 并集占 frame 并集比）。`low_density` 同时看 visual_coverage 与 payload_density（页面完全没有 measured 对象时 payload 下限交给像素层）；`over_dense` 用 payload_density。

级别由统一政策表决定：结构 / 身份 / 逃逸 / 确定性类永远是 error；内容充实度类（`empty_slide` / `sparse_frame` / `telemetry_gap` / `manifest_gap` / `tuning_used` / `page_count_unknown` / `hollow_object` / `edge_ink`）在 `--profile agent` 下升级为 error；审美类保持 warning。

| 诊断 | 级别 | 触发条件 | action |
| --- | --- | --- | --- |
| `content_overflow` | error | fit 为 `overflow`（必然 body_overflow_ratio > 0） | `split_slide` |
| `margin_squeeze` | error | fit 为 `tight`：内容靠吃掉外边距才放得下 | `trim_or_split` |
| `gap_compressed` | warning | fit 为 `compressed`：语义间隙被压到 preferred 之下 | `trim_or_set_mode_compact` |
| `invalid_fit_state` | error | fit 状态与数值不变量矛盾（导出器坏了或遥测被伪造） | `report_bug` |
| `object_escapes_frame` | error | `overflow_x` 为真；payload 横向探出自身 frame；normal/compressed 下 payload 纵向探出 | `trim_content` |
| `object_outside_body` | error | 横向越界任何 fit 状态都查；纵向越界只在 normal / compressed 下查 | `trim_content` |
| `frame_integrity` | error | 帧状态机被破坏：缺步、重复步、steps 与 frame_count 不符、子页不连续、handout 非末帧、record 页码不是末帧页 | `report_bug` |
| `orphan_frame` | error | 某帧联结不到任何 record（deck 级） | `report_bug` |
| `duplicate_slide_id` | error | 两页共用一个 id，帧无法归属（deck 级） | `use_unique_ids` |
| `empty_frame` | error | 某个真实渲染帧一个对象都不显示 | `fix_reveal_order` |
| `sparse_frame` | warning¹ | 早期帧的可见墨水低于该 archetype 下限的一半 | `fix_reveal_order` |
| `semantic_pair_split` | error | 语义对间距（按可见墨水量）超出 proximity 上界 | `set_mode_compact` |
| `object_overlap` | error / warning¹ | 相关对轴向重叠且二维相交（error）；无关块按真实渲染帧检查（agent 下 error） | `split_slide` |
| `empty_shell` | error | 某对象 measured payload 面积趋近于零 | `add_content` |
| `underfilled_card` | warning | 大色块卡片里几乎没有内容（一个词占 60% 高的卡） | `add_content_or_merge` |
| `low_density` | warning | visual_coverage 或 payload_density 低于该 archetype 下限 | `merge_or_enlarge_visual` |
| `over_dense` | warning | payload_density 高于 0.80 | `split_slide` |
| `hollow_frame` | warning | natural 视觉的 payload 在任一轴占 frame 不足一半 | `change_visual_fit` |
| `column_imbalance` | warning | 行版式列 preferred 高度的相对差 > 0.55 且绝对差 > 0.12 | `rebalance_columns` |
| `crowded_related_pair` | warning | 语义对间距低于下界（fit 非 normal 时不报） | `set_mode_separated` |
| `wide_gutter` / `weak_relation_alignment` | warning | 水平 gutter 过宽 / 跨轴中心偏差超 0.10 | `reduce_gutter` / `align_pair` |
| `invalid_relation_direction` | warning | 关系逆着阅读顺序（from 在 to 下方/右侧） | `review_manually` |
| `missing_relation_target` | error | 关系引用不存在的对象 id | `report_bug` |
| `trapped_whitespace` | warning | 相邻无关块之间垂直间隙超过 0.30 | `declare_relation_or_reduce_gap` |
| `content_clustered_top` / `_bottom` | warning | 加权重心偏离且对应方向留白过大 | `recenter_content` |
| `header_shrunk` / `header_overflow` | warning / error | 页头标题缩过 / 缩到 0.65 仍放不下或纵向撞页头带 | `shorten_title` |
| `telemetry_gap` | warning¹ | 内容页没有布局遥测（只认联结成功的帧，handout 安全） | `use_layout_component` |
| `manifest_gap` | warning¹ | 物理页缺页面清单（总页数来自像素渲染或 `--page-count`） | `use_slide_layouts` |
| `manifest_duplicate` | error | 同一物理页有两条页面清单 | `report_bug` |
| `page_count_unknown` | warning¹ | 没有总页数来源，清单完整性不可判 | `pass_page_count` |
| `tuning_used` | warning¹ | 该页覆盖了 `tuning`（契约保留给人工） | `remove_tuning` |

¹ `--profile agent` 下升级为 error。

解析是 fail-closed 的：bbox 缺字段、paint 带负尺寸或缺 `paint_fill`、未知 kind / role / state / payload_source、`visible_from` 越界、record 内对象 id 重复、relations 不是列表或 kind / axis / proximity 不在封闭集、旧版 schema，全部以输入错误退出（exit 2），不产生"带默认值的报告"。`--rules` 覆盖文件校验到叶子：标量必须是有限数字（bool 不算数字），proximity 区间必须是 `0 <= lo <= hi` 的两元列表，未知规则名拒绝。

退出码：输入损坏 2；存在 error 诊断 1（`--strict` 下 warning 也算）；`--advisory` 恒 0。遥测为空（deck 完全没用布局组件）直接非零。

阈值是以 demo 的 good 页为锚的启发式初值（good 页全部通过、bad 页各自命中），可用 `--rules rules.json` 覆盖。`--dump-features features.json` 导出每页的扁平指标向量，供将来按历史优秀 deck 的分布（分位数而非均值，focus 单独建分布）校准阈值；在指标本身修正之前采样的旧语料不要复用。

## 像素交叉验证

```bash
scripts/xwysyy-check deck.typ --pixels            # 几何 + 像素一次跑完
scripts/xwysyy-check deck.typ --profile agent     # agent 下像素强制启用
```

渲染真实 PNG，做三类几何遥测看不到的检查。页面坐标换算全部来自 `<xwysyy-frame>` v2 导出的物理版心几何，不再硬编码模板 margin 常量；每个物理页先联结到它的 (record, reveal step)，只有 `visible_from <= step` 的对象参与解释墨迹：

1. **`render_telemetry_mismatch`**（恒 error）：版心内、当前步可见对象的 frame 之外出现墨水。`place(...)` 逃逸、内容画出分配框、以及**在自己步数之前提前出现的内容**（逃进未来对象的空槽也算）都会被抓到。
2. **`edge_ink`**（agent 下 error）：页面外缘带出现墨水（横向溢出、裁切嫌疑）。除了面积阈值，还有滑动窗口的行峰值检测，单独一行贴边的长 token / URL 也会被抓到。全出血页（title / section / end / image）按页面清单豁免。
3. **`hollow_object`**（agent 下 error）：逐对象验证——在 record 的末帧页上，检查每个对象 payload 框内是否有真实墨迹，**排除页面背景与该对象自己的卡片填色**（`paint_fill`）。空 stretch 视觉、`hide(...)`、卡片背景撑起来的假 payload 都在这里现形。declared payload 的唯一证据就来自这一步。

像素层同时给覆盖率检查提供真实总页数（`manifest_gap` / `page_count_unknown` 精确化）。几何遥测是主循环；human profile 下 `--pixels` 用于发版前或遥测与渲染疑似不一致时，agent profile 恒开。

## AI 调参循环

```bash
scripts/xwysyy-check deck.typ --profile agent --format json
```

按诊断的 `action` 修正：`split_slide`（拆页或删字）、`change_visual_fit`（图改 `visual()` + `fit: "contain"` 撑满）、`merge_or_enlarge_visual`（放大主视觉、补说明或并页）、`rebalance_columns`（长列单独成页）、`set_mode_compact`（收紧 mode）、`use_layout_component`（手写页改回组件）、`shorten_title`（标题改短）、`fix_reveal_order`（先亮实质内容块）、`add_content`（给空槽填真内容）。调完重新跑，直到无 error；warning 由人工判断。`content_clustered_*` 一般不该出现（组件已分配好），出现说明用了手写坐标，改回组件。`report_bug` 类（frame_integrity / orphan_frame / render_telemetry_mismatch / invalid_fit_state）不该靠改内容消掉——它们意味着导出器或遥测本身出了问题。

## 生成契约

**禁止**：手写 `#v(...)` 制造大间距；用绝对坐标或 `place` 控制普通正文；用 `align(bottom)` 把正文推到底部；在一页里堆多个无约束 block；**修改任何组件的 `tuning` 字典**（数字微调属于人工层，`extra.tuned` 会出卖你）；**在布局组件内容里使用 `#pause` / `#meanwhile` / 全局 `#uncover`**（touying 会 panic，分步展示改用组件的 `reveal: true`）；给 `xwysyy-slide` 传 `kind`（参数已删除，会 panic；豁免页只能用 `outline-slide` / `title-slide` 等专用版式）；用 spacer / 空字符串 / `hide(...)` / 空 stretch 视觉填充槽位（编译期 panic 或像素层 `hollow_object`）。

**必须**：图文上下结构用 `duo-slide`；单一结论少内容用 `focus-slide`；多列对等信息用 `grid-slide`；多块同节奏用 `stack-slide`；左右对比用 `compare-slide`；一行关键数字用 `stat-slide`（条目用 `metric(value, label)`）；图配 caption 与结论用 `figure-slide`；窄标签配宽内容用 `sidebar-slide`（传纯内容，不包 `textbox`）；要撑满的视觉显式写 `visual(...)`，固有尺寸的图用 `image(width: 100%)`；分步展示用 `reveal: true`（精确步数用 `reveal-from`，显式值恒优先）；只通过 `mode: compact | balanced | separated` 调密度；编译后跑 `scripts/xwysyy-check deck.typ --profile agent`（像素强制启用），按返回的 action 修正，不靠"看起来差不多"停止迭代。

两个使用面：AI 走上面的契约（agent profile 把内容充实度类诊断全部当 error，且强制像素验证）；人类维护者可以用 `tuning` 微调数值、用默认 human profile 把覆盖率当 warning 处理。

通过 Universe 包安装时，检查工具位于包缓存内（Linux 默认 `~/.cache/typst/packages/preview/xwysyy/<version>/scripts/`）；克隆仓库使用则直接跑 `scripts/xwysyy-check`。
