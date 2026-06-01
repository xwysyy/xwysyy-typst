# AI 配色生成器

将下方提示词复制到任意多模态 AI（Claude、ChatGPT、Gemini 等），附上你的参考材料，即可生成可直接粘贴到 `src/themes.typ` 的主题配置。

## 支持的输入

- 一张 PPT / 网页 / 海报 / 学校官网截图
- 一份 PDF 文件（如已有的演示文稿）
- 配色网站的调色板链接或截图
- 文字描述（如"深绿色学术风"、"我的学校主色是 #003366"、"类似 Apple Keynote 的简洁风"）
- 以上任意组合

## 提示词

将以下内容整体复制，连同你的参考材料一起发送给 AI：

---

````
我正在使用一个 Typst slide 主题（xwysyy-typst），需要你帮我设计一套自定义配色方案。

## 输出格式

请严格按以下 Typst 代码格式输出主题配置，可直接粘贴到 src/themes.typ 的 themes 字典中：

```typst
my-theme: (
  sea: rgb("#______"),
  sky: rgb("#______"),
  skyl: rgb("#______"),
  skyll: rgb("#______"),
  paper: rgb("#______"),
  header-fill: rgb("#______"),
  header-text: rgb("#______"),
  page-fill: rgb("#______"),
),
```

## 8 个颜色字段的用途

| 字段 | 用途 | 视觉位置 |
|------|------|---------|
| `sea` | 主色（最深）| 表格首行背景、章节标题块、链接色、列表一级标记 ❖ |
| `sky` | 强调色 | 列表二级标记 ⬦、end-slide 强调短线 |
| `skyl` | 浅色背景 | 备用浅底色 |
| `skyll` | 最浅背景 | 代码块底色、表格偶数行底色、textbox 组件底色 |
| `paper` | 浅色文字 | 深色块（表格首行、focus-slide、章节标题块）上的文字 |
| `header-fill` | 顶栏背景 | 每页顶部标题栏的背景色 |
| `header-text` | 顶栏文字 | 每页顶部标题栏的文字色 |
| `page-fill` | 页面背景 | 整个 slide 页面的底色 |

## 配色硬约束（必须遵守）

1. **亮度阶梯**：sea（最深）→ sky → skyl → skyll（最浅），同色系逐级变浅
2. **深色块文字对比度**：paper 在 sea 上的 WCAG AA 对比度 >= 4.5:1
3. **顶栏文字对比度**：header-text 在 header-fill 上的 WCAG AA 对比度 >= 4.5:1
4. **背景区分度**：page-fill 必须比 skyll 明显更浅（不可相同），否则代码块和 textbox 无法从背景中辨别
5. **header-fill 和 header-text 设为 `none` 时**：表示使用默认值（header-fill = sea，header-text = paper），适合深色顶栏风格

## 设计原则（基于实战经验，务必遵循）

### 色温统一
整套配色的色温（暖/冷）必须一致。常见错误是主色偏红/暖，但浅色用了偏蓝/冷的灰白——这会产生"两套感觉"。如果 sea 是暖色（红/橙/棕），那 skyl、skyll、page-fill 也应该偏暖（奶白、米白、粉白），不要用纯白或蓝白。

### 顶栏轻重
顶栏（header）是每页都出现的元素。如果顶栏用深色实底（header-fill = sea），视觉上会"压住"页面，标题栏比内容更吸引注意力。两种处理方式：
- **深色顶栏**（适合冷色/蓝色系）：header-fill 设为 `none`（回退 sea），header-text 设为 `none`（回退 paper），经典深底白字
- **浅色顶栏**（适合暖色系）：header-fill 用浅色（如米色、浅粉），header-text 用 sea 或接近 sea 的深色，让标题栏"退到背景"而不喧宾夺主

### 组件区分度
page-fill、skyll（textbox/代码块底色）、skyl 三者需要有视觉上可辨别的差异。如果太接近，用户分不出哪里是代码块、哪里是文本框、哪里是背景。建议：
- page-fill 最浅（接近白）
- skyll 稍深一点（有微弱底色）
- skyl 再深一档（明显有色底）

### 整体协调感检查
生成后自检这些场景的视觉和谐度：
- 表格：sea 底首行 + skyll 底数据行，过渡是否自然？
- 代码块：skyll 底色在 page-fill 背景上是否能看出边界？
- focus-slide：sea 满屏底色 + paper 大字，是否舒适不刺眼？

## 内置主题参考

以下两套主题已经过反复调试验证，可作为设计参照：

**sky（冷蓝色系，深色顶栏）**：
```
sea: #3b60a0, sky: #bdd0f1, skyl: #eff3ff, skyll: #f4f9ff
paper: #f5f6f8, header-fill: none, header-text: none, page-fill: white
```

**sunset（暖红色系，浅色顶栏）**：
```
sea: #970014, sky: #D8A6A2, skyl: #fdf0f0, skyll: #FFF8F6
paper: #f5f6f8, header-fill: #F7EEE7, header-text: #970014, page-fill: #fffefd
```

## 请输出

1. **主题名称**（英文小写，1-2 个单词，如 forest / coral / midnight / glacier）
2. **完整配置代码块**（Typst 格式，可直接粘贴）
3. **一句话风格描述**
4. **自检报告**：逐项确认上述 5 条硬约束和 4 个场景检查都通过

如果参考材料中有多种配色方向，请给出 2-3 套方案供我选择，每套都要包含自检报告。
````

---

## 使用生成的主题

1. 打开 `src/themes.typ`，找到顶部的 `themes` 字典
2. 在最后一个主题条目后追加新主题：

```typst
#let themes = (
  sky: ( ... ),
  sunset: ( ... ),
  forest: (
    sea: rgb("#2d5016"),
    sky: rgb("#8cb369"),
    skyl: rgb("#e8f5e0"),
    skyll: rgb("#f5faf2"),
    paper: rgb("#f5f6f8"),
    header-fill: none,
    header-text: none,
    page-fill: white,
  ),
)
```

3. 在 deck 中使用：

```typst
#show: xwysyy-pre.with(
  theme: "forest",
  config-info( ... ),
)
```

4. 编译验证：`typst compile --root . your-deck.typ`

## 从现有主题微调

如果只想小改内置主题的某几个颜色，把现有配置和你的需求一起发给 AI：

````
基于 xwysyy-typst 的 sunset 主题微调：

```
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
```

我想把主色从酒红改成 [你的描述]，其他颜色跟着协调调整。
请输出完整的新配置，并附自检报告。
````
