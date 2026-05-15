# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-05-14

### Added

- 7 种 slide 版式：封面（`title-slide`）、目录（`outline-slide`）、章节过渡（`new-section-slide`）、内容页（`xwysyy-slide`）、焦点页（`focus-slide`）、全屏图片（`image-slide`）、结束页（`end-slide`）
- `outline-slide` 目录页支持自动收集 `=` 一级标题，也可手动传入章节数组
- `textbox` 多列等高文本框组件（基于 `components.lazy-layout`）
- 内置 **sky**（蓝色调）和 **sunset**（暖红色调）两套配色方案
- `red` / `bred` / `yellow` / `byellow` 四个颜色强调宏
- CJK 合成斜体（逐字符 synthetic skew）
- 笔记模式 `xwysyy-note`（A4 学术笔记排版，主题无关）
- 箭头符号自动替换（`->` / `=>` / `<=>` 等）
- AI 配色生成器文档（`docs/THEME-GENERATOR.md`）

### Changed

- 禁用 slide 模式的图片自动阴影 show rule，避免 `layout` / `measure` 与 touying slides 组合时的兼容性问题

### Removed

- 移除 `card` 组件；多列等高内容改用 `textbox`
