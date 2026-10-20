# Core CS Notes — study guide

Renders the DSA, OOP, OS, DBMS, CN, Resume Skills, System Design, Product & Analytics, SQL Interview Lab, Probability & Statistics, Product Casebook, Analytics Engineering and Machine Coding handbooks as a chapter/section study site
(Next.js 16 + Fumadocs).

    npm run study    # build + serve at http://localhost:3000 (light on RAM; rerun after editing notes)
    npm run dev      # live reload, but needs several GB of free RAM

`scripts/sync-notes.mjs` copies the notes into `content/docs/` (generated, gitignored) before every
`dev`/`build`. Edited a note? Rerun `npm run study`. The source notes in `../*/Notes` are only ever
read — the sync never writes back to them.

## Deploying

The sync script reads `../DSA Notes`, `../OOP Notes` and so on, which sit **outside** this folder.
So the repository root must be the parent directory (the one containing both `study-guide/` and the
source `* Notes/` folders), with the host's **root directory set to `study-guide`**. On Vercel that is
Project Settings → Build → Root Directory. Deploying `study-guide/` alone fails at `prebuild`,
because `../*/Notes` would not exist.

The site is fully static apart from `/api/search`, so no environment variables or services are
needed.

## Structure

Each subject in `SUBJECTS` (in the sync script) becomes a `root: true` folder, so the sidebar only
ever shows one subject; the dropdown at the top of the sidebar switches between them. A subject's
`groups` become collapsible sidebar folders, and `index` is the chapter used as its landing page at
`/docs/<subject>`.

Group folders exist for the sidebar only — `slugs` in `lib/source.ts` strips them from the URL, so
`dsa/trees-heaps/trees.md` serves at `/docs/dsa/trees`.

The sync script fails loudly on a chapter that is in no group, and on an unknown Lucide icon name
(the icon registry it checks is what the Fumadocs plugin resolves against — `Building2` exists in
`lucide-react` but not in that registry).

To add a subject: add an entry to `SUBJECTS`, plus its tag in `components/search-dialog.tsx`. The
home page picks subjects up from the page tree on its own.

## Two upstream workarounds

- `tabMode="top"` (subject tabs in the navbar) renders the tabs but blanks the page body — it adds a
  grid child with no grid area, collapsing the content column. Leave it off.
- `components/search-dialog.tsx` replaces Fumadocs' default search dialog, which renders its footer
  (holding the tag filter) as a sibling of the portaled popup. Passing `tags` through
  `RootProvider` therefore leaks a stray filter row onto every page instead of showing it in the
  dialog.
