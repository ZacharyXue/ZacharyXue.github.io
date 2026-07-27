# AGENTS.md — ZacharyXue.github.io 项目规范

## 项目概述

基于 [Astro](https://astro.build) 的静态个人主页，部署在 GitHub Pages (`https://zacharyxue.github.io`)。

## 技术栈

- **框架**: Astro v5（静态站点生成器）
- **内容**: Markdown + Content Collections
- **样式**: CSS（全局变量 + scoped styles）
- **部署**: GitHub Actions → GitHub Pages
- **语言**: TypeScript (config), Markdown (content), Astro (pages)

## 目录结构

```
.
├── public/                     # 静态文件，构建时原样输出
│   ├── index.html              # 主页（纯 HTML）
│   ├── style.css               # 主页样式
│   └── exports/                # 外部工具导出的 HTML
├── src/
│   ├── content/                # Markdown 内容
│   │   ├── blog/               # 博客文章
│   │   ├── docs/               # 知识文档
│   │   └── projects/           # 项目介绍
│   ├── layouts/                # Astro 布局组件
│   │   ├── BlogLayout.astro
│   │   ├── DocLayout.astro
│   │   └── ProjectLayout.astro
│   ├── pages/                  # 路由页面
│   │   ├── blog/
│   │   ├── docs/
│   │   ├── projects/
│   │   └── custom/             # 手写特殊样式页面
│   └── styles/
│       └── global.css          # 全局主题和 Markdown 排版
├── astro.config.mjs
├── .github/workflows/deploy.yml
├── docs/                       # 项目相关文档（非网站内容）
└── AGENTS.md                   # 本文件
```

## 如何添加内容

### 添加博客文章

1. 在 `src/content/blog/` 下创建 `YYYY-MM-DD-slug.md`
2. 文件命名必须使用 kebab-case，日期前缀必须与 `date` frontmatter 一致

```markdown
---
title: 文章标题
date: 2026-06-15
tags: [技术, 前端]
description: 文章摘要，用于 SEO 和列表预览
draft: false
---

正文内容...
```

- `draft: true` 的文章不会出现在列表页，不会被构建
- slug 从文件名自动提取（去掉日期前缀和 .md 后缀）
- 图片放在 `public/` 下，Markdown 中相对路径引用：`![alt](/image-name.png)`

### 添加文档

1. 在 `src/content/docs/` 下创建 `slug.md`
2. `order` 控制文档列表排序

```markdown
---
title: 文档标题
order: 1
---

文档内容...
```

### 添加项目

1. 在 `src/content/projects/` 下创建 `project-slug.md`

```markdown
---
title: 项目名称
url: https://github.com/user/repo
tags: [开源, Rust]
status: active
---

项目描述...
```

### 添加自定义 HTML 页面

- **外部工具导出的 HTML**: 直接放入 `public/exports/`，访问路径 `/exports/filename.html`
- **手写特殊样式页面**: 在 `src/pages/custom/` 下创建 `name.astro`，访问路径 `/custom/name`

```astro
---
// 自定义页面的逻辑
---

<html>
  <!-- 完全自定义的 HTML，<style> 自动 scoped -->
</html>

<style>
  /* 自动 scoped，不影响全局 */
</style>
```

## 样式规范

- **全局主题**: `src/styles/global.css` 定义 CSS 变量和 Markdown 排版
- **配色**: `--primary-color: #2c3e50`, `--secondary-color: #3498db`, `--bg-color: #ecf0f1`
- **布局组件**: 使用 `src/layouts/` 下的布局文件，保持导航和页脚一致
- **自定义页面**: `.astro` 文件中的 `<style>` 块自动 scoped，不污染其他页面
- **外部 HTML**: 样式完整保留，独立 namespace
- **响应式**: 所有页面需适配移动端（使用现有 `@media` 断点 768px）

## 开发命令

```bash
npm run dev        # 启动开发服务器 (http://localhost:4321)
npm run build      # 构建到 dist/
npm run preview    # 预览构建结果
```

## 构建 & 部署

- **自动部署**: 推送到 `main` 分支后，GitHub Actions 自动构建并部署
- **手动部署**: `npm run build` 后 `dist/` 目录即为站点内容
- **本地预览**: `npm run build && npm run preview`

## 新增依赖

```bash
npm install <package-name>
```

如需 Astro 集成（如 `@astrojs/sitemap`、`@astrojs/rss`），先在 `astro.config.mjs` 中配置。

## 文件命名约定

- Markdown 文件：kebab-case
- Astro 组件/页面：PascalCase (如 `BlogLayout.astro`)
- 静态资源：kebab-case 或原始文件名

## 注意事项

- 不要在 `src/content/` 外创建 Markdown 文件
- `public/` 下的文件会原样输出，不要放构建产物
- `docs/` 仅放项目相关文档，不是网站内容
- 提交前务必运行 `npm run build` 验证不报错
- Content Collections 的 frontmatter 字段必须与 `src/content/config.ts` 中的 schema 一致

## 天天基金 ttskill CLI

当用户问题涉及天天基金、基金账户、持仓、收益、交易查询、选基、行情观点、资产配置等能力时，使用本机 `ttskill` 命令。

- **CLI 路径**: `~/.local/bin/ttskill`（已在 PATH 中）
- **路由查看**: `ttskill agent-entry show`
- **路由刷新**: `ttskill agent-entry refresh --env prod`
- **业务调用**: `ttskill invoke <skill_id>`（需先 login 授权）
- **登录**: `ttskill login`

分类只用于理解和路由，不是可调用 Skill。最终必须选择具体原子 `skill_id`。
