import { defineConfig } from 'astro/config';
import rehypeSlug from 'rehype-slug';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://zacharyxue.github.io',
  base: '/',
  markdown: {
    rehypePlugins: [rehypeSlug],
    shikiConfig: {
      // 亮 / 暗色双主题，跟随页面主题切换
      themes: {
        light: 'github-light',
        dark: 'github-dark',
      },
      wrap: true,
    },
  },
  integrations: [sitemap()],
});