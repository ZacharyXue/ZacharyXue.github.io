# Homepage Redesign Spec

**Date**: 2026-06-03
**Status**: approved

## Goal

Replace the current single-page landing (`public/index.html`) with a blog-style homepage. The homepage becomes a blog post list (`/`), and a shared base layout eliminates duplicated navigation code.

## Non-goals

- No pagination (defer until post volume warrants it)
- No search, tags filter, or RSS (separate features)
- No dark mode toggle

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `src/layouts/BaseLayout.astro` | Shared layout: `<html>` shell, sticky nav, footer. Accepts `title`, `description` props and a `<slot>` for page body. |
| `src/pages/index.astro` | Homepage — fetches non-draft blog posts, renders as a list. Replaces `public/index.html`. |
| `src/pages/about.astro` | About Me page — handwritten Astro page with a standard framework (avatar placeholder, intro, social links). Content filled by user. |

### Modified Files

| File | Change |
|------|--------|
| `src/layouts/BlogLayout.astro` | Wraps with `BaseLayout` instead of duplicating nav/footer HTML. |
| `src/layouts/DocLayout.astro` | Same as above. |
| `src/layouts/ProjectLayout.astro` | Same as above. |
| `src/pages/blog/index.astro` | Wraps with `BaseLayout` instead of inline nav/footer. |
| `src/pages/docs/index.astro` | (reviewed for consistency) |
| `src/pages/projects/index.astro` | (reviewed for consistency) |
| `src/styles/global.css` | Update CSS variables for clean white theme. Remove unused styles if any. |

### Deleted Files

| File | Reason |
|------|--------|
| `public/index.html` | Replaced by `src/pages/index.astro`. |
| `public/style.css` | Only referenced by the now-deleted `index.html`. |

---

## Component Details

### BaseLayout.astro

```
Props:
  title: string          — page title (appended with "| Zachary Xue")
  description?: string   — meta description (optional)

Slots:
  default — page body content

Nav links:
  首页 → /
  全部文章 → /blog
  文档 → /docs
  项目 → /projects
  关于我 → /about
```

**Nav behavior**:
- Fixed/sticky top, white background, bottom border (`1px solid #eee`).
- Logo "Zachary Xue" on the left links to `/`.
- Five nav links on the right.
- Current page link highlighted in blue (`--accent-color`) via `aria-current="page"` or Astro's `Astro.url.pathname` check.

### Homepage (`src/pages/index.astro`)

```
Data: getCollection('blog'), filter draft=false, sort by date desc
Layout: BaseLayout(title="首页")
Content:
  - <h1>Blog</h1> or similar heading
  - List of posts, each showing:
    * Title (linked to /blog/{slug})
    * Date (formatted zh-CN)
    * Description (if provided)
  - Empty state message if no posts
```

### About Page (`src/pages/about.astro`)

```
Layout: BaseLayout(title="关于我")
Content framework:
  - Avatar placeholder area
  - Name / tagline
  - Intro paragraph (user fills in)
  - Social links section (GitHub, email, etc. — user fills in)
```

---

## Visual Style

**Theme**: Clean white-background minimal (tech blog style).

### CSS Variables (`global.css`)

```css
:root {
  --primary-color: #333;
  --accent-color: #3498db;
  --text-color: #333;
  --text-muted: #999;
  --bg-color: #ffffff;
  --border-color: #eee;
  --font-mono: 'SF Mono', 'Fira Code', monospace;
  --max-width: 720px;
}
```

### Key style decisions

- **No dark nav background** — white nav with bottom border only.
- **No hero gradient, no card shadows** — flat, text-focused layout.
- **Links**: `--accent-color` (#3498db) with no underline by default, underline on hover.
- **Post list items**: separated by `1px solid var(--border-color)` bottom border, consistent vertical spacing.
- **Footer**: simple centered text, muted color, light top border.

### Responsive

- Mobile breakpoint: 768px.
- Nav links reduce gap, no hamburger menu (horizontal scroll if needed).
- Content area: `max-width: 720px`, centered with `padding: 0 1rem`.

---

## Acceptance Criteria

1. Visiting `/` shows a list of published (non-draft) blog posts in reverse chronological order.
2. Navigation is consistent across all pages (home, blog, docs, projects, about) — same markup, no duplication.
3. `/about` renders a styled page with placeholder content.
4. `npm run build` completes without errors.
5. `public/index.html` and `public/style.css` are removed.
6. All existing pages (blog post, doc, project) continue to render correctly.
7. Mobile view is usable at 375px width.
