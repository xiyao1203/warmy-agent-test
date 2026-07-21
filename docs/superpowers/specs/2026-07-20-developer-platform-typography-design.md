# 专业开发者平台字体体系设计规格

## 目标

将 Warmy Agent 测试平台从偏传统管理后台的文字观感，升级为接近 Linear、Vercel 和 GitHub Developer Platform 的专业开发者工具字体体系。全站统一字体资源、字号、字重、行高、文字颜色与数字排版，不修改业务逻辑、组件结构、布局尺寸、品牌色、状态色、背景或边框体系。

## 方案比较

1. Token 优先兼容层：加载真实字体资源，建立语义 Typography Token，同时让现有 Tailwind 字号工具类映射到同一尺度，再定向迁移标题、说明、表格和代码区域。覆盖完整、改动可控，采用此方案。
2. Typography React 组件：新增 `PageTitle`、`SectionTitle`、`Body` 等组件并逐页替换。语义明确，但会大规模改变 JSX 和 DOM，布局回归风险过高。
3. 全局元素选择器：直接重写 `h1`、`h2`、`p`、`code`。改动最少，但无法区分落地页、工作台、弹窗和紧凑表格，不满足语义 Token 要求。

## 字体交付

- 使用 Next.js 内置 `next/font/google` 加载 `Geist`、`Geist_Mono` 和 `Noto_Sans_SC`，由 Next.js 在构建时下载并随应用自托管，运行时不访问外部字体 CDN。
- 根布局将三个字体变量挂载到 `<html>`，确保所有路由、Portal 浮层和主题均继承同一字体上下文。
- UI 字体栈：`var(--font-geist), "Source Han Sans SC", var(--font-noto-sans-sc), "Noto Sans SC", sans-serif`。
- 技术字体栈：`var(--font-geist-mono), "Source Code Pro", monospace`。
- `Source Han Sans SC` 保留为本机优先中文 fallback；未安装时使用应用自托管的 `Noto Sans SC`。
- 仅加载正常体可变字重，覆盖 400、500、600；使用 `font-display: swap`，不引入独立字体运行时依赖。

## Typography Token

在 `tokens.css` 中建立可复用的字体族与排版 Token，在 `globals.css` 中提供语义工具类。Token 同时暴露字号、字重、行高和字距，禁止只替换 `font-family`。

| 语义类 | 字号 | 字重 | 行高 | 字距 |
| --- | ---: | ---: | ---: | ---: |
| `text-page-title` | 26px | 600 | 36px | -0.02em |
| `text-section-title` | 18px | 600 | 28px | 0 |
| `text-card-title` | 16px | 600 | 24px | 0 |
| `text-body` | 14px | 400 | 22px | 0 |
| `text-secondary` | 13px | 400 | 20px | 0 |
| `text-caption` | 12px | 500 | 18px | 0 |
| `text-code` | 13px | 400 | 22px | 0 |

语义类使用稳定 CSS 类名，不依赖页面自定义任意值。现有 Tailwind 尺度同步到同一基础尺度：

- `text-xs` 对齐 Caption 的 `12/18`。
- `text-sm` 对齐 Body 的 `14/22`。
- `text-base` 对齐 Card Title 尺寸的 `16/24`，字重仍由调用方决定。
- `text-lg` 对齐 Section Title 尺寸的 `18/28`。
- `text-2xl` 对齐 Page Title 尺寸的 `26/36`。

这一兼容层让存量页面立即获得统一行高；语义类负责表达标题、正文、辅助文本和代码的明确职责。

## 文字颜色

只更新文字语义 Token，不改变品牌色、状态色、背景、表面、边框和阴影。

| 语义 | 现有变量 | Light | Dark |
| --- | --- | --- | --- |
| 一级文字 | `--ink` | `#101828` | `#F5F7FA` |
| 二级文字 | `--body` | `#344054` | `#D0D5DD` |
| 正文 | `--muted` | `#475467` | `#98A2B3` |
| 辅助 | `--muted-soft` | `#667085` | `#667085` |

已有兼容别名继续指向这些语义变量，不增加页面级十六进制颜色。

## 组件规则

### 页面与内容层级

- 工作区页面标题统一使用 `text-page-title`。
- 区块标题使用 `text-section-title`。
- 卡片、面板和默认模型标题使用 `text-card-title`。
- 页面说明和表单正文使用 `text-body`。
- 时间、描述、帮助文本和弱化元信息使用 `text-secondary`。
- 标签、状态辅助文字和紧凑元数据使用 `text-caption`。
- 落地页 Hero 保留现有展示字号，避免改变首屏构图，但继承新字体与文字颜色 Token。

### 导航

- 普通菜单：14px / 400。
- 选中菜单：14px / 600。
- 菜单分类标题：12px / 500 / `0.02em`。
- 不修改导航行高、图标尺寸、侧栏宽度或分组结构。

### 按钮

- 公共 Button 默认使用 14px / 600。
- 图标按钮继续依赖可访问名称和 Tooltip，不增加可见文字。
- 不修改控制高度、内边距、圆角和交互状态。

### 表格与状态

- 表头：13px / 500 / 20px。
- 表格内容：14px / 400 / 22px。
- Badge 与状态 Tag：12px / 500 / 18px。
- 不修改列宽、行高策略、分页位置或表格结构；通过截图验证字体变化未引起遮挡。

### 技术内容

- `code`、`pre`、`samp` 以及 Prompt、JSON、API、Trace、Log、测试执行详情和 Token 统计使用 Geist Mono。
- `kbd` 继续保留 UI 字体，避免快捷键提示过度技术化；代码块和结构化数据使用 `text-code` 的 13/22 尺度。
- 技术内容允许横向滚动或已有截断策略，不因字体迁移改变容器布局。

## 数字排版

- 根 UI 启用 `font-variant-numeric: tabular-nums`，统一百分比、耗时、Token、页码、日期和指标宽度。
- 代码区域同时启用 `font-variant-ligatures: none`，避免日志、ID 和代码符号产生歧义。
- 不改变数字格式化、单位、精度或业务计算。

## 迁移边界

- 优先修改根布局、Token、全局排版工具、Sidebar、Button、Table、Badge 和共用页面标题模式。
- 定向迁移管理后台页面标题、区块标题、页面说明、辅助文本和技术内容；不机械替换所有 JSX。
- 保留营销落地页已有展示层级、对话内容的语义结构和帮助页面的特殊排版，只接入字体、基础行高和颜色 Token。
- 不修改 API、数据库、权限、路由、状态管理、业务组件数据流或依赖版本。
- 本任务不包含上一轮尚未实施的操作图标缩小与分页下拉方向调整。

## 无障碍与可读性

- Light/Dark 均使用已确认的四级文字色，状态信息继续保留文本或图标，不以颜色作为唯一表达。
- 字号不低于 12px，正文行高不低于 1.5 倍附近，支持中文长文本和英文技术标识混排。
- 字体加载失败时回退到本地无衬线和等宽字体，页面保持可读和可操作。
- 不移除焦点状态、ARIA 标签、Tooltip 或屏幕阅读器文本。

## 测试与验收

- Token 测试覆盖字体栈、七级语义 Typography Token、Light/Dark 四级文字色和数字等宽规则。
- 根布局测试确认三个 Next Font 变量应用到 `<html>`，不产生运行时 CDN 请求。
- 公共组件测试覆盖 Sidebar 普通/选中字重、分类标题、Button、Table Header/Cell、Badge 与技术内容语义类。
- Playwright 检查登录落地页、模型配置或代表性列表页、测试 Agent、运行中心在 Light/Dark 下的计算字体、字号、行高和颜色。
- 在 1280、1440 和 390px 检查标题换行、导航截断、表格密度、按钮文本和浮层文字，不允许出现关键内容遮挡或页面级横向滚动。
- 运行前端 format、lint、typecheck、全量组件测试、关键 Playwright 和生产构建。
