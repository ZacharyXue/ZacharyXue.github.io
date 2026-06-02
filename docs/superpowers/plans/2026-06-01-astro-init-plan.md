# Astro 静态站点初始化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建基于 Astro 的 GitHub Pages 个人主页项目骨架，包含 Content Collections、3 种内容类型布局、部署工作流，并产出 AGENTS.md 和 docs/。

**Architecture:** Astro 作为 SSG，`src/content/` 管理 Markdown 内容（blog/docs/projects 三个 Collection），`public/` 存放现有 HTML/CSS 及外部导出文件，GitHub Actions 构建后部署到 gh-pages。

**Tech Stack:** Astro, TypeScript (Content Collections config), Markdown, GitHub Actions

---

### Task 1: 初始化项目骨架

**Files:**
- Create: `package.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`
- Modify: `.gitignore`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "zacharyxue.github.io",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^5.0.0"
  }
}
```

- [ ] **Step 2: 创建 astro.config.mjs**

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://zacharyxue.github.io',
  base: '/',
});
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist", "node_modules"]
}
```

- [ ] **Step 4: 更新 .gitignore**

```
node_modules/
dist/
.astro/
.superpowers/
.DS_Store
```

- [ ] **Step 5: 安装依赖并验证**

```bash
npm install
```

- [ ] **Step 6: 验证项目能初始化**

```bash
npx astro build
```
Expected: 构建成功（可能输出空 dist，因尚无页面）

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json astro.config.mjs tsconfig.json .gitignore
git commit -m "feat: initialize Astro project skeleton"
```

---

### Task 2: 迁移现有主页到 public/

**Files:**
- Create: `public/index.html`
- Create: `public/style.css`
- Delete: `index.html` (根目录)
- Delete: `style.css` (根目录)

- [ ] **Step 1: 移动现有文件到 public/**

```bash
mkdir -p public
mv index.html public/index.html
mv style.css public/style.css
```

- [ ] **Step 2: 验证构建**

```bash
npx astro build
```
Expected: 构建成功，`dist/` 下包含 `index.html` 和 `style.css`

- [ ] **Step 3: Commit**

```bash
git add public/ && git rm index.html style.css
git commit -m "feat: migrate existing homepage to public/"
```

---

### Task 3: 创建 Content Collections 配置

**Files:**
- Create: `src/content/config.ts`
- Create: `src/content/blog/.gitkeep`
- Create: `src/content/docs/.gitkeep`
- Create: `src/content/projects/.gitkeep`
- Create: `src/content/blog/2026-06-01-hello-world.md` (示例文章)
- Create: `src/content/docs/getting-started.md` (示例文档)
- Create: `src/content/projects/sample-project.md` (示例项目)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p src/content/blog src/content/docs src/content/projects
```

- [ ] **Step 2: 创建 src/content/config.ts**

```ts
import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.date(),
    tags: z.array(z.string()).default([]),
    description: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

const docsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    order: z.number().default(0),
    parent: z.string().optional(),
  }),
});

const projectsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    url: z.string().optional(),
    tags: z.array(z.string()).default([]),
    status: z.enum(['active', 'archived']).default('active'),
    image: z.string().optional(),
  }),
});

export const collections = {
  blog: blogCollection,
  docs: docsCollection,
  projects: projectsCollection,
};
```

- [ ] **Step 3: 创建示例博客 src/content/blog/2026-06-01-hello-world.md**

```markdown
---
title: Hello World
date: 2026-06-01
tags: [随笔]
description: 第一篇博客文章
---

欢迎来到我的博客！这是第一篇文章。
```

- [ ] **Step 4: 创建示例文档 src/content/docs/getting-started.md**

```markdown
---
title: 快速开始
order: 1
---

这里放使用指南、环境配置等文档内容。
```

- [ ] **Step 5: 创建示例项目 src/content/projects/sample-project.md**

```markdown
---
title: 示例项目
url: https://github.com/ZacharyXue
tags: [开源]
status: active
---

项目简介和说明。
```

- [ ] **Step 6: 验证 Content Collections 类型检查**

```bash
npx astro build
```
Expected: 构建成功，无类型错误

- [ ] **Step 7: Commit**

```bash
git add src/content/
git commit -m "feat: add Content Collections config with blog, docs, projects schemas"
```

---

### Task 4: 创建全局样式和布局组件

**Files:**
- Create: `src/styles/global.css`
- Create: `src/layouts/BlogLayout.astro`
- Create: `src/layouts/DocLayout.astro`
- Create: `src/layouts/ProjectLayout.astro`

- [ ] **Step 1: 创建 src/styles/global.css**

```css
:root {
  --primary-color: #2c3e50;
  --secondary-color: #3498db;
  --text-color: #333;
  --bg-color: #ecf0f1;
  --white: #ffffff;
  --max-width: 800px;
  --font-mono: 'SF Mono', 'Fira Code', monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.8;
  color: var(--text-color);
  background-color: var(--bg-color);
}

/* Markdown content styles */
article {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 2rem 1rem;
}

article h1 { font-size: 2rem; color: var(--primary-color); margin-bottom: 1rem; }
article h2 { font-size: 1.5rem; color: var(--primary-color); margin: 2rem 0 0.8rem; }
article h3 { font-size: 1.2rem; margin: 1.5rem 0 0.6rem; }
article p { margin-bottom: 1rem; }
article a { color: var(--secondary-color); text-decoration: none; }
article a:hover { text-decoration: underline; }
article ul, article ol { margin: 0 0 1rem 1.5rem; }
article li { margin-bottom: 0.3rem; }
article code {
  background: #f0f0f0;
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}
article pre {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 1rem;
}
article pre code {
  background: none;
  padding: 0;
  color: inherit;
}
article blockquote {
  border-left: 4px solid var(--secondary-color);
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  background: #f8f9fa;
  border-radius: 0 4px 4px 0;
}
article img {
  max-width: 100%;
  border-radius: 4px;
}
```

- [ ] **Step 2: 创建 src/layouts/BlogLayout.astro**

```astro
---
import '/src/styles/global.css';

export interface Props {
  frontmatter: {
    title: string;
    date: Date;
    tags?: string[];
    description?: string;
  };
}

const { frontmatter } = Astro.props;
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{frontmatter.title} | Zachary Xue</title>
  <meta name="description" content={Astro.props.frontmatter.description} />
</head>
<body>
  <nav class="navbar">
    <a href="/" class="logo">Zachary Xue</a>
    <div class="nav-links">
      <a href="/">首页</a>
      <a href="/blog">博客</a>
      <a href="/docs">文档</a>
      <a href="/projects">项目</a>
    </div>
  </nav>

  <article>
    <header class="article-header">
      <h1>{frontmatter.title}</h1>
      <time datetime={frontmatter.date.toISOString().slice(0, 10)}>
        {frontmatter.date.toLocaleDateString('zh-CN')}
      </time>
      {frontmatter.tags?.length > 0 && (
        <div class="tags">
          {frontmatter.tags.map(tag => (
            <span class="tag">{tag}</span>
          ))}
        </div>
      )}
    </header>
    <div class="article-body">
      <slot />
    </div>
  </article>

  <footer>
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>

<style>
  .navbar {
    background: var(--primary-color);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .logo {
    color: var(--white);
    font-weight: bold;
    font-size: 1.2rem;
    text-decoration: none;
  }
  .nav-links { display: flex; gap: 1.5rem; }
  .nav-links a {
    color: var(--white);
    text-decoration: none;
    font-size: 0.95rem;
  }
  .nav-links a:hover { color: var(--secondary-color); }
  .article-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #ddd;
  }
  .article-header time {
    color: #888;
    font-size: 0.9rem;
  }
  .tags { margin-top: 0.8rem; display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }
  .tag {
    background: var(--secondary-color);
    color: var(--white);
    padding: 0.2em 0.7em;
    border-radius: 12px;
    font-size: 0.8rem;
  }
  footer {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-size: 0.85rem;
  }
  @media (max-width: 768px) {
    .navbar { padding: 1rem; }
    .nav-links { gap: 1rem; }
    article { padding: 1rem; }
  }
</style>
```

- [ ] **Step 3: 创建 src/layouts/DocLayout.astro**

```astro
---
import '/src/styles/global.css';

export interface Props {
  frontmatter: {
    title: string;
  };
}

const { frontmatter } = Astro.props;
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{frontmatter.title} | 文档 | Zachary Xue</title>
</head>
<body>
  <nav class="navbar">
    <a href="/" class="logo">Zachary Xue</a>
    <div class="nav-links">
      <a href="/">首页</a>
      <a href="/blog">博客</a>
      <a href="/docs">文档</a>
      <a href="/projects">项目</a>
    </div>
  </nav>

  <div class="doc-container">
    <aside class="doc-sidebar">
      <a href="/docs" class="back-link">&larr; 文档首页</a>
    </aside>
    <article>
      <h1>{frontmatter.title}</h1>
      <div class="article-body">
        <slot />
      </div>
    </article>
  </div>

  <footer>
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>

<style>
  .navbar {
    background: var(--primary-color);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .logo {
    color: var(--white);
    font-weight: bold;
    font-size: 1.2rem;
    text-decoration: none;
  }
  .nav-links { display: flex; gap: 1.5rem; }
  .nav-links a {
    color: var(--white);
    text-decoration: none;
    font-size: 0.95rem;
  }
  .nav-links a:hover { color: var(--secondary-color); }
  .doc-container {
    display: flex;
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1rem;
    gap: 2rem;
  }
  .doc-sidebar {
    width: 220px;
    flex-shrink: 0;
  }
  .back-link {
    display: inline-block;
    color: var(--secondary-color);
    text-decoration: none;
    padding: 0.5rem 0;
  }
  .back-link:hover { text-decoration: underline; }
  article { flex: 1; min-width: 0; padding: 0; }
  footer {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-size: 0.85rem;
  }
  @media (max-width: 768px) {
    .doc-container { flex-direction: column; }
    .doc-sidebar { width: 100%; }
  }
</style>
```

- [ ] **Step 4: 创建 src/layouts/ProjectLayout.astro**

```astro
---
import '/src/styles/global.css';

export interface Props {
  frontmatter: {
    title: string;
    url?: string;
    tags?: string[];
    status?: string;
  };
}

const { frontmatter } = Astro.props;
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{frontmatter.title} | 项目 | Zachary Xue</title>
</head>
<body>
  <nav class="navbar">
    <a href="/" class="logo">Zachary Xue</a>
    <div class="nav-links">
      <a href="/">首页</a>
      <a href="/blog">博客</a>
      <a href="/docs">文档</a>
      <a href="/projects">项目</a>
    </div>
  </nav>

  <article>
    <header class="project-header">
      <h1>{frontmatter.title}</h1>
      <div class="project-meta">
        {frontmatter.status && (
          <span class={`status status-${frontmatter.status}`}>
            {frontmatter.status === 'active' ? '活跃' : '归档'}
          </span>
        )}
        {frontmatter.url && (
          <a href={frontmatter.url} target="_blank" rel="noopener" class="project-link">项目链接 &rarr;</a>
        )}
      </div>
      {frontmatter.tags?.length > 0 && (
        <div class="tags">
          {frontmatter.tags.map(tag => (
            <span class="tag">{tag}</span>
          ))}
        </div>
      )}
    </header>
    <div class="article-body">
      <slot />
    </div>
  </article>

  <footer>
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>

<style>
  .navbar {
    background: var(--primary-color);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .logo {
    color: var(--white);
    font-weight: bold;
    font-size: 1.2rem;
    text-decoration: none;
  }
  .nav-links { display: flex; gap: 1.5rem; }
  .nav-links a {
    color: var(--white);
    text-decoration: none;
    font-size: 0.95rem;
  }
  .nav-links a:hover { color: var(--secondary-color); }
  .project-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #ddd;
  }
  .project-meta {
    display: flex;
    gap: 1rem;
    justify-content: center;
    align-items: center;
    margin-top: 0.8rem;
  }
  .status {
    padding: 0.2em 0.7em;
    border-radius: 12px;
    font-size: 0.8rem;
  }
  .status-active { background: #27ae60; color: white; }
  .status-archived { background: #95a5a6; color: white; }
  .project-link { color: var(--secondary-color); text-decoration: none; font-size: 0.9rem; }
  .project-link:hover { text-decoration: underline; }
  .tags { margin-top: 0.8rem; display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }
  .tag {
    background: var(--secondary-color);
    color: var(--white);
    padding: 0.2em 0.7em;
    border-radius: 12px;
    font-size: 0.8rem;
  }
  footer {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-size: 0.85rem;
  }
  @media (max-width: 768px) {
    .navbar { padding: 1rem; }
    .nav-links { gap: 1rem; }
    article { padding: 1rem; }
  }
</style>
```

- [ ] **Step 5: 验证构建**

```bash
npx astro build
```
Expected: 构建成功

- [ ] **Step 6: Commit**

```bash
git add src/styles/ src/layouts/
git commit -m "feat: add global styles and layout components for blog, docs, projects"
```

---

### Task 5: 创建列表页和详情页路由

**Files:**
- Create: `src/pages/blog/index.astro`
- Create: `src/pages/blog/[slug].astro`
- Create: `src/pages/docs/index.astro`
- Create: `src/pages/docs/[slug].astro`
- Create: `src/pages/projects/index.astro`
- Create: `src/pages/projects/[slug].astro`

- [ ] **Step 1: 创建 src/pages/blog/index.astro**

```astro
---
import { getCollection } from 'astro:content';
import BlogLayout from '/src/layouts/BlogLayout.astro';

const posts = (await getCollection('blog'))
  .filter(p => !p.data.draft)
  .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>博客 | Zachary Xue</title>
  <link rel="stylesheet" href="/src/styles/global.css" />
</head>
<body>
  <nav style="background: #2c3e50; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;">
    <a href="/" style="color: white; font-weight: bold; font-size: 1.2rem; text-decoration: none;">Zachary Xue</a>
    <div style="display: flex; gap: 1.5rem;">
      <a href="/" style="color: white; text-decoration: none;">首页</a>
      <a href="/blog" style="color: #3498db; text-decoration: none;">博客</a>
      <a href="/docs" style="color: white; text-decoration: none;">文档</a>
      <a href="/projects" style="color: white; text-decoration: none;">项目</a>
    </div>
  </nav>

  <main style="max-width: 800px; margin: 0 auto; padding: 3rem 1rem;">
    <h1 style="font-size: 2rem; color: #2c3e50; margin-bottom: 2rem;">博客</h1>
    {posts.length === 0 ? (
      <p style="color: #888;">还没有文章。</p>
    ) : (
      <ul style="list-style: none; padding: 0;">
        {posts.map(post => {
          const slug = post.id.replace(/^\d{4}-\d{2}-\d{2}-/, '').replace(/\.md$/, '');
          return (
            <li style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee;">
              <a href={`/blog/${slug}`} style="text-decoration: none;">
                <h2 style="font-size: 1.3rem; color: #2c3e50; margin-bottom: 0.3rem;">{post.data.title}</h2>
              </a>
              <time style="color: #888; font-size: 0.85rem;">{post.data.date.toLocaleDateString('zh-CN')}</time>
              {post.data.description && (
                <p style="color: #666; margin-top: 0.4rem; font-size: 0.95rem;">{post.data.description}</p>
              )}
            </li>
          );
        })}
      </ul>
    )}
  </main>

  <footer style="text-align: center; padding: 2rem; color: #888; font-size: 0.85rem;">
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>
```

- [ ] **Step 2: 创建 src/pages/blog/[slug].astro**

```astro
---
import { getCollection } from 'astro:content';
import BlogLayout from '/src/layouts/BlogLayout.astro';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map(post => {
    const slug = post.id.replace(/^\d{4}-\d{2}-\d{2}-/, '').replace(/\.md$/, '');
    return { params: { slug }, props: { post } };
  });
}

const { post } = Astro.props;
const { Content } = await post.render();
---

<BlogLayout frontmatter={post.data}>
  <Content />
</BlogLayout>
```

- [ ] **Step 3: 创建 src/pages/docs/index.astro**

```astro
---
import { getCollection } from 'astro:content';

const docs = (await getCollection('docs'))
  .sort((a, b) => a.data.order - b.data.order);
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>文档 | Zachary Xue</title>
  <link rel="stylesheet" href="/src/styles/global.css" />
</head>
<body>
  <nav style="background: #2c3e50; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;">
    <a href="/" style="color: white; font-weight: bold; font-size: 1.2rem; text-decoration: none;">Zachary Xue</a>
    <div style="display: flex; gap: 1.5rem;">
      <a href="/" style="color: white; text-decoration: none;">首页</a>
      <a href="/blog" style="color: white; text-decoration: none;">博客</a>
      <a href="/docs" style="color: #3498db; text-decoration: none;">文档</a>
      <a href="/projects" style="color: white; text-decoration: none;">项目</a>
    </div>
  </nav>

  <main style="max-width: 800px; margin: 0 auto; padding: 3rem 1rem;">
    <h1 style="font-size: 2rem; color: #2c3e50; margin-bottom: 2rem;">文档</h1>
    {docs.length === 0 ? (
      <p style="color: #888;">还没有文档。</p>
    ) : (
      <ul style="list-style: none; padding: 0;">
        {docs.map(doc => (
          <li style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #eee;">
            <a href={`/docs/${doc.id.replace(/\.md$/, '')}`} style="text-decoration: none;">
              <h2 style="font-size: 1.2rem; color: #2c3e50;">{doc.data.title}</h2>
            </a>
          </li>
        ))}
      </ul>
    )}
  </main>

  <footer style="text-align: center; padding: 2rem; color: #888; font-size: 0.85rem;">
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>
```

- [ ] **Step 4: 创建 src/pages/docs/[slug].astro**

```astro
---
import { getCollection } from 'astro:content';
import DocLayout from '/src/layouts/DocLayout.astro';

export async function getStaticPaths() {
  const docs = await getCollection('docs');
  return docs.map(doc => ({
    params: { slug: doc.id.replace(/\.md$/, '') },
    props: { doc },
  }));
}

const { doc } = Astro.props;
const { Content } = await doc.render();
---

<DocLayout frontmatter={doc.data}>
  <Content />
</DocLayout>
```

- [ ] **Step 5: 创建 src/pages/projects/index.astro**

```astro
---
import { getCollection } from 'astro:content';

const projects = await getCollection('projects');
---

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>项目 | Zachary Xue</title>
  <link rel="stylesheet" href="/src/styles/global.css" />
</head>
<body>
  <nav style="background: #2c3e50; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;">
    <a href="/" style="color: white; font-weight: bold; font-size: 1.2rem; text-decoration: none;">Zachary Xue</a>
    <div style="display: flex; gap: 1.5rem;">
      <a href="/" style="color: white; text-decoration: none;">首页</a>
      <a href="/blog" style="color: white; text-decoration: none;">博客</a>
      <a href="/docs" style="color: white; text-decoration: none;">文档</a>
      <a href="/projects" style="color: #3498db; text-decoration: none;">项目</a>
    </div>
  </nav>

  <main style="max-width: 1000px; margin: 0 auto; padding: 3rem 1rem;">
    <h1 style="font-size: 2rem; color: #2c3e50; margin-bottom: 2rem;">项目</h1>
    {projects.length === 0 ? (
      <p style="color: #888;">还没有项目。</p>
    ) : (
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;">
        {projects.map(project => (
          <div style="background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <a href={`/projects/${project.id.replace(/\.md$/, '')}`} style="text-decoration: none;">
              <h2 style="font-size: 1.2rem; color: #2c3e50; margin-bottom: 0.5rem;">{project.data.title}</h2>
            </a>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
              {project.data.tags?.map(tag => (
                <span style="background: #3498db; color: white; padding: 0.15em 0.6em; border-radius: 10px; font-size: 0.75rem;">{tag}</span>
              ))}
            </div>
            {project.data.status && (
              <span style={`font-size: 0.8rem; color: ${project.data.status === 'active' ? '#27ae60' : '#95a5a6'};`}>
                {project.data.status === 'active' ? '● 活跃' : '● 归档'}
              </span>
            )}
          </div>
        ))}
      </div>
    )}
  </main>

  <footer style="text-align: center; padding: 2rem; color: #888; font-size: 0.85rem;">
    <p>&copy; 2026 Zachary Xue</p>
  </footer>
</body>
</html>
```

- [ ] **Step 6: 创建 src/pages/projects/[slug].astro**

```astro
---
import { getCollection } from 'astro:content';
import ProjectLayout from '/src/layouts/ProjectLayout.astro';

export async function getStaticPaths() {
  const projects = await getCollection('projects');
  return projects.map(project => ({
    params: { slug: project.id.replace(/\.md$/, '') },
    props: { project },
  }));
}

const { project } = Astro.props;
const { Content } = await project.render();
---

<ProjectLayout frontmatter={project.data}>
  <Content />
</ProjectLayout>
```

- [ ] **Step 7: 验证构建**

```bash
npx astro build
```
Expected: 构建成功，`dist/` 下包含 `/blog`, `/docs`, `/projects` 路由及详情页

- [ ] **Step 8: Commit**

```bash
git add src/pages/
git commit -m "feat: add collection listing and detail pages for blog, docs, projects"
```

---

### Task 6: 创建 GitHub Actions 部署工作流

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: 创建 .github/workflows/deploy.yml**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions deploy workflow for GitHub Pages"
```

---

### Task 7: 创建 AGENTS.md

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: 创建 AGENTS.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md project specification"
```

---

### Task 8: 创建 docs/ 目录

**Files:**
- Create: `docs/index.md`

- [ ] **Step 1: 创建 docs/index.md**

```markdown
# 项目文档

## 索引

- [Astro 迁移设计规范](superpowers/specs/2026-06-01-astro-migration-design.md)
- [实现计划](superpowers/plans/2026-06-01-astro-init-plan.md)

## 说明

`docs/` 目录存放与项目相关的较重任务文档，如设计规范、实现计划、架构决策记录等。

这些文档**不是**网站内容，不会出现在最终构建的静态站点中。
```

- [ ] **Step 2: Commit**

```bash
git add docs/
git commit -m "docs: add docs/ directory with index"
```

---

### Task 9: 最终验证

- [ ] **Step 1: 完整构建验证**

```bash
npm run build
```
Expected: 构建成功，`dist/` 包含：
- `index.html` + `style.css`（原主页）
- `blog/index.html`、`blog/hello-world/index.html`
- `docs/index.html`、`docs/getting-started/index.html`
- `projects/index.html`、`projects/sample-project/index.html`

- [ ] **Step 2: 验证路由正确性**

检查 `dist/` 下 HTML 文件中的链接是否正确指向对应路径。

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: final verification - all pages build correctly"
```
```

**Expected:** 构建成功，所有页面可以正常访问。
