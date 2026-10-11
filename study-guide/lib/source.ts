import { loader, type LoaderPlugin } from 'fumadocs-core/source';
import { createElement, type FC } from 'react';
import { icons } from 'lucide-react';
import { docsRoute } from './shared';
import { defineDocs } from 'fumadocs-mdx/macro';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';
import { z } from 'zod';

/**
 * Same as fumadocs' own lucideIconsPlugin, but tags the <svg> with its icon name
 * so global.css can colour it. Done as a data attribute rather than a class
 * because Tailwind only emits classes it can see literally in the source.
 */
function lucideIconsPlugin(): LoaderPlugin {
  // Generic so each transform hands back the node type it was given.
  const resolve = <T extends { icon?: unknown }>(node: T): T => {
    if (typeof node.icon !== 'string') return node;
    const name = node.icon;
    const Icon = icons[name as keyof typeof icons] as FC<Record<string, unknown>> | undefined;
    // sync-notes.mjs validates icon names too; fail loudly rather than silently
    // dropping an icon the sidebar was meant to have.
    if (!Icon) throw new Error(`unknown lucide icon "${name}"`);
    node.icon = createElement(Icon, { 'data-icon': name });
    return node;
  };
  return {
    name: 'notes:coloured-icons',
    transformPageTree: { file: resolve, folder: resolve, separator: resolve },
  };
}

const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    schema: pageSchema.extend({ part: z.number().default(0) }),
  },
  meta: {
    schema: metaSchema,
  },
});

export const source = loader({
  baseUrl: docsRoute,
  source: docs.toFumadocsSource(),
  plugins: [lucideIconsPlugin()],
  // Group folders exist to make the sidebar collapsible, not to lengthen URLs:
  // dsa/trees-heaps/trees -> /docs/dsa/trees
  slugs: (_file, next) => {
    const parts = next();
    return parts.length > 2 ? [parts[0], parts.at(-1)!] : parts;
  },
});

/** Subject slug of a page, used as its search tag. */
export const subjectOf = (page: { slugs: string[] }) => page.slugs[0] ?? '';
