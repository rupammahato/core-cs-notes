import Link from 'next/link';
import { source } from '@/lib/source';
import { getPageTreeRoots, type Folder, type Node } from 'fumadocs-core/page-tree';

/** The subject's landing page: its folder index, or failing that its first page. */
function landingUrl(folder: Folder): string | undefined {
  if (folder.index) return folder.index.url;
  for (const node of folder.children) {
    if (node.type === 'page') return node.url;
    if (node.type === 'folder') {
      const nested = landingUrl(node);
      if (nested) return nested;
    }
  }
}

const countPages = (nodes: Node[]): number =>
  nodes.reduce(
    (n, node) =>
      n + (node.type === 'page' ? 1 : node.type === 'folder' ? countPages(node.children) : 0),
    0,
  );

export default function HomePage() {
  const subjects = getPageTreeRoots(source.getPageTree()).filter(
    (root): root is Folder => root.type === 'folder',
  );

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-12 md:py-20">
      <p className="text-sm font-medium text-fd-primary">Study guide</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">Core CS Notes</h1>
      <p className="mt-3 max-w-2xl text-fd-muted-foreground">
        Pick a subject, then a chapter from the sidebar. Press{' '}
        <kbd className="rounded border bg-fd-muted px-1.5 py-0.5 font-mono text-xs">Ctrl K</kbd> to
        search across everything.
      </p>

      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        {subjects.map((subject) => {
          const groups = subject.children.filter((n): n is Folder => n.type === 'folder');
          const chapters = countPages(subject.children);

          return (
            <Link
              key={subject.$id}
              href={landingUrl(subject) ?? '/docs'}
              className="group rounded-xl border bg-fd-card p-6 transition-all duration-200 hover:-translate-y-0.5 hover:border-fd-primary/60 hover:bg-fd-accent hover:shadow-lg hover:shadow-fd-primary/5"
            >
              <div className="flex items-center gap-3">
                {subject.icon && (
                  // The icon carries its own hue from lib/source.ts; the badge
                  // tints itself to match via currentColor.
                  <span className="subject-badge inline-flex size-10 shrink-0 items-center justify-center rounded-lg [&_svg]:size-5">
                    {subject.icon}
                  </span>
                )}
                <h2 className="text-lg font-semibold group-hover:text-fd-primary">
                  {subject.name}
                </h2>
              </div>
              {subject.description && (
                <p className="mt-3 text-sm text-fd-muted-foreground">{subject.description}</p>
              )}
              <p className="mt-4 font-mono text-xs text-fd-muted-foreground">
                {chapters} {chapters === 1 ? 'chapter' : 'chapters'} · {groups.length}{' '}
                {groups.length === 1 ? 'group' : 'groups'}
              </p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {groups.map((group) => (
                  <span
                    key={group.$id}
                    className="inline-flex items-center gap-1.5 rounded-md border bg-fd-muted/60 px-2 py-0.5 text-xs text-fd-muted-foreground [&_svg]:size-3"
                  >
                    {group.icon}
                    {group.name}
                  </span>
                ))}
              </div>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
