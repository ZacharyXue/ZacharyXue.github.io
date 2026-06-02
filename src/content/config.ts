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
