# Astro 静态站点迁移设计

**日期:** 2026-06-01
**状态:** 待实现

---

## 1. 背景与目标

将当前纯 HTML/CSS 的 GitHub Pages 个人主页迁移到 Astro 静态站点生成器，以支持：

- **Markdown 内容管理**：博客文章、知识文档、项目介绍
- **自定义 HTML 页面**：外部工具导出的 HTML + 手写特殊样式页面
- **可持续扩展**：中等体量（上百篇文章），定期更新

当前状态：`index.html` + `style.css` 为核心的简单静态站。

---

## 2. 技术选型

**选定：Astro**（已用户确认）

替代方案：
- 11ty：更轻量但无 Content Collections 类型安全
- 纯手动：零依赖但扩展性差

选 Astro 的理由：
- Content Collections 为博客/文档/项目提供类型安全的 Markdown 管理
- `public/` 目录直出原始文件（外部 HTML 零处理）
- `.astro` 文件支持 scoped CSS 和组件复用
- 默认零 JS 输出，性能优秀
- GitHub Actions 原生支持部署

---

## 3. 目录结构

```
ZacharyXue.github.io/
├── public/                        # 静态文件，构建时原样复制到根路径
│   ├── index.html                 # 当前主页，迁移到此
│   ├── style.css                  # 主页自有样式
│   └── exports/                   # 外部工具导出的 HTML 文件
├── src/
│   ├── content/                   # Markdown 内容（Content Collections）
│   │   ├── blog/                  # 博客文章
│   │   ├── docs/                  # 知识文档
│   │   └── projects/              # 项目介绍
│   ├── layouts/                   # 布局组件
│   │   ├── BlogLayout.astro
│   │   ├── DocLayout.astro
│   │   └── ProjectLayout.astro
│   ├── pages/                     # 页面（自动路由）
│   │   ├── blog/[slug].astro      # 博客详情页
│   │   ├── docs/[slug].astro      # 文档详情页
│   │   ├── custom/                # 手写特殊样式页面
│   │   └── index.astro            # 新主页（可选，可继续用 public/index.html）
│   └── styles/
│       └── global.css             # 全局主题变量
├── astro.config.mjs
├── package.json
├── .github/workflows/deploy.yml   # 自动部署
├── AGENTS.md                      # 项目规范
├── docs/                          # 项目相关文档
└── .gitignore                     # 排除 node_modules, .superpowers 等
```

---

## 4. Content Collections Frontmatter Schema

### Blog (`src/content/blog/`)

```yaml
---
title: 文章标题
date: 2026-06-01
tags: [技术, 前端]
description: 文章摘要（用于 SEO 和列表预览）
draft: false
---
```

- 文件命名：`YYYY-MM-DD-slug.md`
- `draft: true` 时构建跳过

### Docs (`src/content/docs/`)

```yaml
---
title: 文档标题
order: 1
parent: 父级文档名（可选，用于层级结构）
---
```

- 文件命名：`slug.md`

### Projects (`src/content/projects/`)

```yaml
---
title: 项目名
url: https://github.com/...
tags: [开源, Rust]
status: active          # active | archived
image: /projects/thumb.png   # 可选，项目截图
---
```

- 文件命名：`project-name.md`

---

## 5. 自定义 HTML 页面处理

| 场景 | 处理方式 | 访问路径 |
|------|----------|----------|
| 外部工具导出 HTML | 放入 `public/exports/` | `/exports/file.html` |
| 手写特殊样式页面 | 创建 `src/pages/custom/name.astro` | `/custom/name` |
| Markdown 内嵌组件 | `.mdx` 文件 + Astro 组件 | 同普通 Markdown 路由 |

---

## 6. 样式约定

- **全局主题变量**：`src/styles/global.css` 定义 CSS 自定义属性（颜色、字体、间距）
- **Markdown 样式**：各 Layout 组件内联 `<style>` 控制文章排版
- **自定义页面**：`.astro` 文件 `<style>` 自动 scoped，不污染其他页面
- **外部 HTML**：自带样式完整保留，独立 namespace
- **响应式**：所有页面默认支持移动端

保留现有配色方案：
- `--primary-color: #2c3e50`
- `--secondary-color: #3498db`
- `--bg-color: #ecf0f1`
- `--text-color: #333`

---

## 7. 构建与部署

GitHub Actions 工作流（`.github/workflows/deploy.yml`）：

```
main 分支 push → checkout → npm install → npm run build → deploy to gh-pages
```

本地开发命令：
```bash
npm run dev      # 启动开发服务器（热更新）
npm run build    # 构建到 dist/
npm run preview  # 预览构建结果
```

---

## 8. 待产出文件

1. **AGENTS.md** — 项目规范文件，面向后续 AI/人工开发
2. **docs/** — 较重任务文档目录
3. **Astro 项目骨架** — package.json, astro.config.mjs, 目录结构
4. **GitHub Actions 部署配置**
5. **Content Collections 配置** — src/content/config.ts

---

## 9. 约束

- 现有 `index.html` 和 `style.css` 作为主页保留，迁移到 `public/`
- `docs/` 仅放项目相关文档，不放网站内容
- 所有 Markdown 使用 kebab-case 命名
- 提交前需本地 `npm run build` 验证不报错
