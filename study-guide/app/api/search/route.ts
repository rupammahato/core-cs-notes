import { source, subjectOf } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// Tagged by subject so search can be scoped once OOP/OS are added.
export const { GET } = createFromSource(source, {
  buildIndex: (page) => ({
    id: page.url,
    url: page.url,
    title: page.data.title,
    description: page.data.description,
    structuredData: page.data.structuredData,
    tag: subjectOf(page),
  }),
});
