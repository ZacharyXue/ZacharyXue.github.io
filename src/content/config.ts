import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.date(),
    tags: z.array(z.string()).default([]),
    description: z.string().optional(),
    draft: z.boolean().default(false),
    hide_from_home: z.boolean().default(false),
    pinned: z.boolean().default(false),
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

const wikiCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    domain: z.string(),
    domainLabel: z.string(),
    created: z.string().default(''),
    updated: z.string().default(''),
    type: z.string().default('concept'),
    tags: z.array(z.string()).default([]),
    sources: z.array(z.string()).default([]),
    confidence: z.string().default(''),
    summary: z.string().default(''),
  }),
});

export const collections = {
  blog: blogCollection,
  projects: projectsCollection,
  wiki: wikiCollection,
};
