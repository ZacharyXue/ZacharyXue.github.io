import { defineConfig } from 'astro/config';
import rehypeSlug from 'rehype-slug';

export default defineConfig({
  site: 'https://zacharyxue.github.io',
  base: '/',
  markdown: {
    rehypePlugins: [rehypeSlug],
  },
});