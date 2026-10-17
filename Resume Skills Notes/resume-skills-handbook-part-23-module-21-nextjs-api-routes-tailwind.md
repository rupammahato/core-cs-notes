# Resume Skills Placement Handbook — Part 23
# Module 21: Next.js, API Routes and Tailwind

**Estimated time: 5–6 hours | Tier: 2 | Requires: M6 HTTP, M7 authentication, M20 React; M3 TypeScript for signatures**

---

## Why this module exists

Your resume names Next.js 14, API routes, Edge Middleware and Tailwind. An interviewer can therefore move from “React builds the screen” to where that screen renders, which code reaches the browser, what happens on navigation, where an API executes, and why a changed record still appears stale.

This chapter follows a placement topic explorer from its route tree through rendering, hydration, data/cache policy, HTTP boundaries and styling. It prioritizes useful resume follow-ups; it does not claim a measured ranking of interview frequency. The worked architecture is a teaching design, not an invented description of your actual project.

**Organizing principle: identify the execution environment, request boundary and cache owner before explaining a Next.js feature.**

---

## 1. What Next.js adds to React

React describes UI from components and inputs. Next.js supplies application conventions around it: routing, layouts, server rendering, build output and server endpoints. Tailwind supplies CSS utilities. TypeScript checks source types. These tools occupy different layers; knowing one does not automatically explain another.

For the explorer, ask four separate questions:

1. Which URL identifies the page or API resource?
2. Which work happens during build, on a server request, or in the browser?
3. Which result can safely be reused, for whom, and until when?
4. Which boundary validates input and enforces permission?

```text
Browser: HTML + CSS + client JavaScript
     | document / navigation / API request
     v
Next.js application
  routing + layouts + server rendering + Route Handlers
     | shared service call or bounded backend request
     v
Domain service / database / external provider
```

Next.js can host a small application's server API or act as a backend for its frontend. A separate backend can remain useful for shared business rules, multiple clients, independent scaling and durable workers. Choose from requirements, not from the assumption that every full-stack application needs two separate HTTP servers.

---

## 2. Version context and verified environment

### 2.1 Three contexts that must stay separate

| Context | Meaning |
| --- | --- |
| Resume | Next.js 14 is the named project context; do not rewrite it as a newer version |
| Independent example | Next.js 14.2.35, React 18.3.1 and Tailwind 3.4.19, pinned for this chapter |
| Handbook website | Its own installed Next.js 16.3.8 / React 19 / Tailwind 4 dependency tree; not upgraded here |

Recorded on **15 October 2026** using Windows and an installed headless Chrome browser:

| Runtime/library | Recorded version |
| --- | --- |
| Node | v22.14.0 |
| next | 14.2.35 |
| react | 18.3.1 |
| react-dom | 18.3.1 |
| tailwindcss | 3.4.19 |
| typescript | 5.9.3 |
| playwright-core | 1.64.1 |
| Chrome | 155.0.8059.40 |

The official support page currently lists Next.js 14 as unsupported. This pinned example exists to explain historical resume behavior, not to recommend a new production deployment. The recorded full dependency audit reports **nine affected packages: two moderate, six high and one critical**; these are package-level audit totals, not nine independently demonstrated exploits. The full report and recommended version changes are in dependency-audit.json. [Next.js support policy](https://nextjs.org/support-policy)

### 2.2 Reproduce the actual checks

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-21-nextjs
npm ci
npm run verify
```

The verifier starts an owned loopback origin, builds the real Next.js application, starts its production server on an ephemeral loopback port, opens an installed Chromium browser and closes everything. Set M21_BROWSER to a compatible executable if Chrome/Edge is elsewhere. Installation needs registry access; runtime experiments use local HTTP. The command rebuilds so build-time artifacts and the controlled origin agree.

No standalone demo server is left running. Port 3000 stays stopped. Docker, cloud resources, real accounts and databases are unused. Generated .next/ and node_modules/ are ignored; source and package-lock.json reproduce the fixture.

### 2.3 What was and was not tested

54 checks passed against a production build: routing, actual HTML/hydration, both API styles, middleware matching, server/client disclosure boundaries, cache behavior, ISR, streaming, error recovery and compiled responsive CSS. This is not evidence of hosted Edge geography, CDN propagation, authenticated tenant isolation, durable writes, Server Actions, deployment readiness, comprehensive accessibility or production performance.

---

## 3. App Router and Pages Router

Next.js 14 supports both routing systems. Identify the directory before explaining an API:

| Concern | App Router | Pages Router |
| --- | --- | --- |
| Page | app/topics/page.tsx | pages/topics.tsx |
| Dynamic page | app/topics/[slug]/page.tsx | pages/topics/[slug].tsx |
| Shared UI | Nested layout.tsx | Commonly _app.tsx and explicit composition |
| Server endpoint | app/api/topics/route.ts | pages/api/topics.ts |
| Endpoint interface | Web Request/Response, named method exports | NextApiRequest/NextApiResponse, default handler |

The example deliberately includes App Router pages and a Pages API endpoint at a different URL. They do not compete for the same path. Never apply a Pages Router signature to an App Router file just because both endpoints start with /api. [App pages/layouts](https://nextjs.org/docs/14/app/building-your-application/routing/pages-and-layouts), [Pages API routes](https://nextjs.org/docs/14/pages/building-your-application/routing/api-routes)

### 3.1 Read the fixture tree

```text
app/
  layout.tsx                 shared document, navigation, global CSS
  page.tsx                   /
  catalog/[slug]/page.tsx     /catalog/node and /catalog/react
  dashboard/layout.tsx       persistent dashboard shell
  dashboard/page.tsx         /dashboard
  dashboard/settings/page.tsx
  cache/page.tsx             request-time cache experiment
  isr/page.tsx               revalidated public output
  stream/page.tsx            explicit Suspense boundary
  broken/page.tsx + error.tsx
  api/topics/[slug]/route.ts
  api/echo/route.ts
  api/revalidate/route.ts    local test control only
pages/api/legacy-echo.ts
components/Counter.tsx + TopicLookup.tsx
lib/topics.ts + contract.ts
middleware.ts
```

A folder alone is not necessarily a public page: page.tsx exposes page UI and route.ts exposes an endpoint. A route group such as (marketing) organizes routes without adding that name to the URL. A [slug] segment captures a value; [...slug] is a catch-all and [[...slug]] also accepts the empty case. Treat captured values as input, not trusted object ownership. [Dynamic routes](https://nextjs.org/docs/14/app/building-your-application/routing/dynamic-routes), [route groups](https://nextjs.org/docs/14/app/building-your-application/routing/route-groups)

---

## 4. Layouts, navigation and state lifetime

A nested layout wraps its matching child routes. The root layout supplies html/body. During client navigation within the same dashboard layout, a client counter inside that layout can survive while page content changes. A template provides a fresh instance on navigation when remount behavior is wanted. Do not use layout persistence as durable storage. [Pages and layouts](https://nextjs.org/docs/14/app/building-your-application/routing/pages-and-layouts)

Exact dashboard shell:

**app/dashboard/layout.tsx**

```tsx
import Link from 'next/link';
import Counter from '../../components/Counter';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <section className="card space-y-6"><h1 className="text-3xl font-bold">Practice dashboard</h1>
    <Counter label="layout counter" />
    <nav aria-label="Dashboard" className="flex gap-4 underline">
      <Link href="/dashboard" prefetch={false}>Overview</Link>
      <Link href="/dashboard/settings" prefetch={false}>Settings</Link>
    </nav><div>{children}</div>
  </section>;
}
```

The browser experiment increments the layout counter, follows Settings using Link, checks a window marker to establish that the document survived, and sees the counter remain one. A full reload resets it to zero. The result follows the component's lifetime, connecting directly to M20 state identity.

Link supports framework navigation and prefetching. The fixture explicitly sets prefetch={false} so background navigation requests do not confuse the cache experiments. That does not disable client navigation. Router methods for the App Router come from next/navigation; old Pages Router examples often use next/router. [Linking and navigating](https://nextjs.org/docs/14/app/building-your-application/routing/linking-and-navigating)

**Interview follow-up:** if a draft must survive leaving the layout, refreshing or another device, define the persistence requirement and appropriate owner. An in-memory layout state answers only the first, limited lifetime question.

---

## 5. Server Components and Client Components

App Router components are Server Components by default. They can perform server data work and render results without shipping their implementation as browser component JavaScript. A Client Component boundary permits state, event handlers and effects. Neither label alone tells you whether the route is prebuilt or rendered per request. [Server Components](https://nextjs.org/docs/14/app/building-your-application/rendering/server-components)

### 5.1 A small client island

**components/Counter.tsx**

```tsx
'use client';
import { useEffect, useState } from 'react';

export default function Counter({ label }: { label: string }) {
  const [count, setCount] = useState(0);
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => { setHydrated(true); }, []);
  return <section aria-label={label} className="space-y-3">
    <p>{label}: <output>{count}</output></p>
    <button className="action" onClick={() => setCount(value => value + 1)}>Increment {label}</button>
    <p data-testid={`${label}-hydrated`}>{hydrated ? 'Hydrated' : 'HTML preview'}</p>
  </section>;
}
```

The 'use client' directive marks a module boundary. Its imports participate in the client graph; placing it at the root can unnecessarily enlarge that graph. On the initial full load, Next.js also supplies an HTML preview for Client Components. They become interactive when their client code hydrates. Therefore “Client Component means no server HTML” is incorrect. [Client Components](https://nextjs.org/docs/14/app/building-your-application/rendering/client-components)

### 5.2 Server data and safe props

**lib/topics.ts**

```typescript
import 'server-only';

const topics = [
  { slug: 'node', title: 'Node.js', summary: 'A runtime for JavaScript outside the browser.' },
  { slug: 'react', title: 'React', summary: 'Components describe UI from current inputs.' },
];

export function listTopics() { return topics.map(topic => ({ ...topic })); }
export function findTopic(slug: string) { return topics.find(topic => topic.slug === slug); }

// A synthetic environment marker verifies non-disclosure; it is not a credential.
export function serverConfigured() { return Boolean(process.env.M21_PRIVATE_MARKER); }
```

The home Server Component calls listTopics directly, then passes ordinary display data to its UI. It does not call its own HTTP API to rediscover the same service. The browser lookup uses the API because it is crossing from the browser to the server. These are two callers of shared server data, not a required extra server-to-self request.

Keep a credential or privileged client in a server-only module. Props crossing into client UI must be serializable by React, and their values can reach the browser. A server-only import catches accidental client imports; it does not make rendered output confidential. A Server Component can be passed as rendered children through a Client Component without that client module importing server implementation. [Composition patterns](https://nextjs.org/docs/14/app/building-your-application/rendering/composition-patterns)

The fixture injects a synthetic private marker and renders only a boolean configuration status. Tests inspect the initial document/RSC data and every generated browser .js file for that exact marker. This proves its absence in this fixture, not universal secret-leak prevention for arbitrary applications.

---

## 6. Initial HTML, hydration and rendering strategies

### 6.1 Trace a full page load

```text
GET /
  -> Next resolves page/layouts
  -> obtains server output + client references
  -> returns HTML and supporting RSC/client information
Browser shows initial HTML
  -> client JavaScript loads
  -> React hydrates client islands
Click counter -> local state -> updated UI
```

The no-JavaScript browser context can read the heading and topics, but clicking the counter does not increment it. The ordinary browser sees the hydration status become Hydrated and the click changes the output to one. Both checks use the real production page, not a simulated component renderer.

Hydration requires the initial client render to agree with the supplied HTML. Reading browser-only data in an effect, or deliberately choosing an appropriate browser-only rendering path, avoids pretending that server code has window/localStorage. Random values, time-zone formatting and invalid markup are useful mismatch suspects; do not hide a mismatch before understanding it. [React hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)

### 6.2 Do not mix these axes

| Term | Core question | Explorer use |
| --- | --- | --- |
| CSR | Does browser JavaScript produce/update this UI? | Interactive lookup result |
| SSR / dynamic rendering | Is HTML computed for this incoming request? | Cookie display dashboard |
| SSG / static rendering | Can output be prepared and reused? | Public topic pages |
| ISR | Can reusable public output be refreshed after the build? | Versioned public ISR lab |
| Streaming | Can available UI arrive before slower work completes? | Held topic section |
| Server/Client Component | Which module environment and capabilities apply? | Server page with client counter |

These are related decisions, not mutually exclusive labels for every component. A prebuilt page can contain a hydrated counter. A request-time page can reuse cached public data. Streaming is a delivery strategy; it does not bypass missing permissions or failed dependencies.

### 6.3 Prebuilt dynamic paths versus request-time data

**app/catalog/[slug]/page.tsx**

```tsx
import { randomUUID } from 'node:crypto';
import { notFound } from 'next/navigation';
import { findTopic, listTopics } from '../../../lib/topics';

export const dynamicParams = false;
export function generateStaticParams() { return listTopics().map(({ slug }) => ({ slug })); }
export default function TopicPage({ params }: { params: { slug: string } }) {
  const topic = findTopic(params.slug);
  if (!topic) notFound();
  return <article className="card space-y-4"><h1 className="text-3xl font-bold">{topic.title}</h1>
    <p>{topic.summary}</p><p>Public topic; prebuilt for the recorded build.</p>
    <p data-testid="static-stamp">{randomUUID()}</p>
  </article>;
}
```

generateStaticParams supplies two known slug values. dynamicParams=false limits this example to those paths. The build manifest confirms both are prebuilt, and repeated document requests reuse the same generated UUID. Unknown slugs return 404. This configuration is deliberate; a dynamic URL segment does not inherently mean request-time rendering.

**app/dashboard/page.tsx**

```tsx
import { cookies } from 'next/headers';
import { randomUUID } from 'node:crypto';

export default function Dashboard() {
  const label = cookies().get('demo_label')?.value.slice(0, 40) || 'Visitor';
  return <section className="space-y-3"><h2 className="text-xl font-semibold">Overview</h2>
    <p data-testid="visitor">Display label: {label}</p><p>This cookie is untrusted display data, not authentication.</p>
    <p data-testid="dynamic-stamp">{randomUUID()}</p>
  </section>;
}
```

The dashboard reads cookies during rendering, so it needs request-time information. Two HTTP requests show different labels and different generated stamps. demo_label is untrusted display data; it is **not a verified session or user identity**. Do not replace the authentication rules from M7 with this display demonstration. [Route segment configuration](https://nextjs.org/docs/14/app/api-reference/file-conventions/route-segment-config)

```json
{
  "next": "14.2.35",
  "prebuiltTopics": [
    "/catalog/node",
    "/catalog/react"
  ],
  "dashboardPrerendered": false,
  "isrRevalidateSeconds": 1
}
```

---

## 7. App Router Route Handlers

A Route Handler is an HTTP endpoint, not a rendered React page. It exports methods such as GET/POST and returns a Response. Use the route's runtime and request context deliberately. In Next.js 14, eligible GET handlers returning Response can be cached; this example explicitly selects dynamic execution and an HTTP no-store header. [Route Handlers](https://nextjs.org/docs/14/app/building-your-application/routing/route-handlers)

**app/api/topics/[slug]/route.ts**

```typescript
import { findTopic } from '../../../../lib/topics';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function GET(_request: Request, { params }: { params: { slug: string } }) {
  const topic = findTopic(params.slug);
  return Response.json(topic || { error: 'Topic not found' }, {
    status: topic ? 200 : 404, headers: { 'Cache-Control': 'no-store' },
  });
}
```

Trace GET /api/topics/node:

1. The router captures node as params.slug.
2. The handler calls the shared server-side data function.
3. It returns a small JSON object with status 200 and an explicit HTTP cache policy.
4. An unknown identifier produces 404; an unsupported POST produces 405.
5. The browser validates the response before displaying its title.

The data set is public and in memory. There is no authentication, database lookup or durable mutation. A real private resource handler must verify the session and authorize the requested object before returning data, even if the page UI already checked something.

### 7.1 A POST endpoint still needs a runtime contract

**lib/contract.ts**

```typescript
export function parseMessage(value: unknown): string | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  if (Object.keys(record).length !== 1 || typeof record.message !== 'string') return null;
  const message = record.message.trim();
  return message.length >= 1 && message.length <= 80 ? message : null;
}
```

**app/api/echo/route.ts**

```typescript
import { parseMessage } from '../../../lib/contract';

export const runtime = 'nodejs';
export async function POST(request: Request) {
  const headers = { 'Cache-Control': 'no-store' };
  if (request.headers.get('content-type')?.split(';')[0].trim() !== 'application/json') {
    return Response.json({ error: 'JSON required' }, { status: 415, headers });
  }
  let value: unknown;
  try { value = await request.json(); }
  catch { return Response.json({ error: 'Malformed JSON' }, { status: 400, headers }); }
  const message = parseMessage(value);
  if (message === null) return Response.json({ error: 'Invalid message' }, { status: 422, headers });
  return Response.json({ message, persisted: false }, { headers });
}
```

The contract requires exactly one string field, trims it and accepts 1–80 characters. The handler distinguishes media type 415, malformed JSON 400 and invalid data 422. TypeScript's unknown forces narrowing but does not validate network bytes by itself.

The echo explicitly reports persisted:false. It does not create a record. It also does not implement an ingress body-size limit: limiting the parsed field length is not a streaming payload limit. Production payload/timeout/rate limits belong at the appropriate ingress/runtime/application boundaries. Revisit [M6](/docs/resume-skills/rest-apis-http) and [M8](/docs/resume-skills/api-security-authorization-multi-tenancy) for the complete request boundary.

---

## 8. Pages Router API routes

**pages/api/legacy-echo.ts**

```typescript
import type { NextApiRequest, NextApiResponse } from 'next';
import { parseMessage } from '../../lib/contract';

export default function handler(request: NextApiRequest, response: NextApiResponse) {
  response.setHeader('Cache-Control', 'no-store');
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ error: 'Method not allowed' });
  }
  if (request.headers['content-type']?.split(';')[0].trim() !== 'application/json') {
    return response.status(415).json({ error: 'JSON required' });
  }
  const message = parseMessage(request.body);
  if (message === null) return response.status(422).json({ error: 'Invalid message' });
  return response.status(200).json({ message, persisted: false });
}
export const config = { api: { bodyParser: { sizeLimit: '1kb' } } };
```

This default handler uses request.method, request.body and response.status().json(). Its configured parser accepts at most 1kb. The App and Pages examples share the same pure parseMessage contract and produce the same valid response, but their framework interfaces and parsing responsibilities differ.

Actual checks cover a successful request, invalid runtime data, unsupported method with Allow: POST, malformed JSON rejected by the parser, and an oversized body rejected with 413. The App handler's request.json() error path is handled explicitly; the Pages parser runs before the handler. Do not assume malformed input always follows identical control flow in both systems.

API routes need a server runtime. A static HTML export alone cannot provide these request handlers. Choose deployment capabilities before proposing a static export for a system that depends on server endpoints. [Pages API route reference](https://nextjs.org/docs/14/pages/building-your-application/routing/api-routes)

---

## 9. Browser API access and the BFF boundary

**components/TopicLookup.tsx**

```tsx
'use client';
import { useState } from 'react';

export default function TopicLookup() {
  const [slug, setSlug] = useState('node');
  const [result, setResult] = useState('Not requested');
  const [pending, setPending] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setResult('Loading');
    try {
      const response = await fetch(`/api/topics/${encodeURIComponent(slug)}`, { cache: 'no-store' });
      if (!response.ok) throw new Error('Request failed');
      const data: unknown = await response.json();
      if (!data || typeof data !== 'object' || !('title' in data) || typeof data.title !== 'string') throw new Error('Invalid response');
      setResult(data.title);
    } catch { setResult('Topic unavailable'); }
    finally { setPending(false); }
  }
  return <form onSubmit={submit} className="space-y-3" aria-label="Topic lookup">
    <label htmlFor="topic-slug" className="block">Topic slug</label>
    <input id="topic-slug" value={slug} onChange={event => setSlug(event.target.value)} maxLength={40}
      className="block w-full rounded border border-slate-500 p-2" />
    <button className="action disabled:opacity-50" disabled={pending}>Look up topic</button>
    <p role="status" aria-live="polite">{result}</p>
  </form>;
}
```

The browser controls the slug, submits a same-origin request, checks response.ok, narrows the returned value and displays a useful failure state. A pending request disables another submission. This small submit-only interaction is not a full client data-cache library or a reproduction of the race fixture from M20.

### 9.1 When Next acts as a backend for the frontend

```text
Browser -> same-origin Next endpoint
              verify session + object permission
              validate operation
              call configured internal backend/provider
              map response to a minimal browser contract
Browser <- useful status/data; provider credential stays server-side
```

A BFF can adapt multiple services to the screen's needs and keep provider credentials off the client. That adds a network boundary, its own timeout/error handling and responsibility for permission. If a Server Component can call the shared service directly, an extra request to its own public endpoint usually adds work without adding a necessary boundary. [Next.js BFF guide](https://nextjs.org/docs/app/guides/backend-for-frontend)

For a real proxy, use a configured/allowlisted upstream, bounded input, an explicit timeout, safe forwarding rules and an error contract. Do not accept an arbitrary destination URL from the browser. Keep retries consistent with the operation's idempotency. Do not put long ingestion or durable scheduled work inside a request that must finish quickly; see M15.

Same-origin requests reduce cross-origin configuration; they do not remove CSRF or authorization concerns. Revisit M7/M8 for cookies, session verification, trusted origins and tenant filters. This fixture tests public lookup and nonpersistent echo, not a production authenticated BFF.

---

## 10. Four caches, four different owners

For Next.js 14, name the layer before saying “Next cached it”:

| Layer | Reused object | Useful distinction |
| --- | --- | --- |
| Request memoization | Matching GET fetch results during a component render | Ends with that render; not a persistent shared record |
| Data Cache | Server fetch data across requests | Can outlive one render and be invalidated/revalidated |
| Full Route Cache | Reusable HTML/RSC route output | Static output differs from a request-time route |
| Router Cache | Browser-held route payload segments | A client navigation cache, not the database |

Route Handler execution is outside the React component render tree, so do not promise component request memoization there. An HTTP Cache-Control header is another policy for browser/proxy caches; it is not a substitute for deciding the server Data Cache policy. [Next.js 14 caching overview](https://nextjs.org/docs/14/app/building-your-application/caching)

### 10.1 Explicit fetch policy

**app/cache/page.tsx**

```tsx
import { headers } from 'next/headers';

async function read(kind: 'cached' | 'live') {
  const url = `${process.env.M21_ORIGIN}/items?kind=${kind}`;
  const options = kind === 'cached'
    ? { cache: 'force-cache' as const, next: { tags: ['m21-public'] } }
    : { cache: 'no-store' as const };
  const response = await fetch(url, options);
  if (!response.ok) throw new Error('Origin unavailable');
  const value: unknown = await response.json();
  if (!value || typeof value !== 'object' || !('version' in value) || typeof value.version !== 'number') throw new Error('Invalid origin response');
  return value.version;
}
export default async function CachePage() {
  headers(); // Request-time page; explicit cached data can still be reused.
  const [cachedA, cachedB, liveA, liveB] = await Promise.all([read('cached'), read('cached'), read('live'), read('live')]);
  return <section className="card space-y-3"><h1 className="text-3xl font-bold">Cache lab</h1>
    <p>Duplicate GET reads in this render, with two different persistent cache policies.</p>
    <output data-testid="cache-values">{JSON.stringify({ cachedA, cachedB, liveA, liveB })}</output>
  </section>;
}
```

The request-time page performs two identical cached GET reads and two identical no-store GET reads. The local origin counts actual incoming requests. This separates duplicate reads within a render from reuse across renders. The origin URL is generated for the owned fixture; users cannot choose an upstream.

In the first render, each URL reaches the origin once. After the origin moves from version one to two, the cached pair stays at one while the live pair becomes two. Next.js 14's contextual defaults are easy to misremember, so this example uses explicit policies. no-store is about persistent data reuse here; it does not turn duplicate GETs in one component render into separate required network requests. [Next.js 14 fetch options](https://nextjs.org/docs/14/app/api-reference/functions/fetch)

```json
{
  "first": {
    "cachedA": 1,
    "cachedB": 1,
    "liveA": 1,
    "liveB": 1
  },
  "afterOriginChange": {
    "cachedA": 1,
    "cachedB": 1,
    "liveA": 2,
    "liveB": 2
  },
  "afterTagInvalidation": {
    "cachedA": 2,
    "cachedB": 2,
    "liveA": 2,
    "liveB": 2
  },
  "originCalls": {
    "cached": 2,
    "live": 3
  }
}
```

Interpret the originCalls values alongside all three page visits: the cached URL was fetched initially and again after tag invalidation; the live URL was fetched once per page render. These counts are local mechanism observations, not latency, capacity or billing measurements.

### 10.2 Cache keys and privacy are architecture decisions

For a public topic catalog, sharing data may be appropriate. For a user's drafts, credits or tenant records, first establish the authorization scope and whether a reusable response could cross that scope. Never globally cache a personalized response because caching improves a benchmark.

When stale data appears, inspect database state, Data Cache policy, generated route output, browser navigation payload and HTTP/CDN policy separately. router.refresh requests updated rendering but does not by itself mean every persistent server cache entry was invalidated. An accurate diagnosis names the stale layer and the operation that changes it. [Next.js 14 router.refresh](https://nextjs.org/docs/14/app/api-reference/functions/use-router)

---

## 11. Revalidation and ISR

### 11.1 Invalidate a public tag after an authorized change

**app/api/revalidate/route.ts**

```typescript
import { revalidateTag } from 'next/cache';

// Test-harness control only; a production invalidation endpoint needs real authorization.
export async function POST(request: Request) {
  if (request.headers.get('x-fixture-key') !== process.env.M21_CONTROL_KEY) {
    return Response.json({ error: 'Forbidden' }, { status: 403 });
  }
  revalidateTag('m21-public');
  return Response.json({ invalidated: 'm21-public' });
}
```

The key is a synthetic local test-control value, generated by the verifier's environment. This endpoint accepts only one fixed public tag. It demonstrates rejection without the key, successful invalidation with it, and a fresh origin read on the next page request. It is not a real session, a general webhook receiver or an authorization design.

In Next.js 14, revalidateTag(tag) invalidates the tagged data for subsequent access. revalidatePath selects a path/layout scope instead. Neither function writes the database, and a Route Handler cannot push a fresh screen into every already-open browser. Decide both server invalidation and client update behavior after a mutation. [14 revalidateTag](https://nextjs.org/docs/14/app/api-reference/functions/revalidateTag), [14 revalidatePath](https://nextjs.org/docs/14/app/api-reference/functions/revalidatePath)

### 11.2 Time-based refresh is not a precise scheduler

**app/isr/page.tsx**

```tsx
export const revalidate = 1;
export default async function IsrPage() {
  const response = await fetch(`${process.env.M21_ORIGIN}/isr`, { next: { revalidate: 1 } });
  if (!response.ok) throw new Error('Origin unavailable');
  const data = await response.json();
  if (typeof data.version !== 'number') throw new Error('Invalid version');
  return <section className="card"><h1 className="text-3xl font-bold">ISR lab</h1>
    <output data-testid="isr-version">{data.version}</output>
  </section>;
}
```

The build manifest records a one-second route interval. The verifier changes the controlled origin version, requests the page until refreshed output appears, and records the distinct versions seen:

```json
{
  "versionsObserved": [
    1,
    3
  ],
  "finalVersion": 3,
  "intervalSeconds": 1
}
```

Expiration permits revalidation when traffic arrives; it is not a guarantee that a background cron refreshes every second. A visitor may see stale output while refresh happens, and a failed refresh can retain the previous successful output. This test establishes eventual new output under successful local conditions; it does not assert a universal ordering of every response during regeneration. [Next.js 14 revalidation](https://nextjs.org/docs/14/app/building-your-application/data-fetching/fetching-caching-and-revalidating)

For resume explanations, distinguish a freshness requirement from a revalidation interval. A public tutorial can tolerate brief staleness; a booking confirmation needs a trusted current transaction result, not a cached page used as the source of truth.

---

## 12. Streaming, loading, not-found and errors

### 12.1 Show useful content while a section waits

**app/stream/page.tsx**

```tsx
import { Suspense } from 'react';

async function HeldSection() {
  const response = await fetch(`${process.env.M21_ORIGIN}/held`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Origin unavailable');
  return <p data-testid="stream-result">Deferred topic ready</p>;
}
export default function StreamPage() {
  return <section className="card space-y-3"><h1 className="text-3xl font-bold">Streaming lab</h1>
    <Suspense fallback={<p role="status">Waiting for held topic</p>}><HeldSection /></Suspense>
  </section>;
}
```

The origin holds the dependent request until the verifier releases it. The browser observes the Suspense fallback before that release, then sees Deferred topic ready replace it. This establishes actual progressive delivery, rather than treating a spinner after a fully completed request as proof of streaming.

loading.tsx provides a route segment loading boundary; explicit Suspense can isolate smaller slow sections. Their placement decides what can become visible while work waits. Streaming can expose already-ready structure, but does not make the slow operation faster. [Loading UI and streaming](https://nextjs.org/docs/14/app/building-your-application/routing/loading-ui-and-streaming)

### 12.2 Expected absence and unexpected failure differ

The known catalog configuration returns 404 for an unknown public topic. An API communicates a missing resource through its status/JSON contract. A failed server dependency belongs in an error path rather than an empty successful list.

**app/broken/error.tsx**

```tsx
'use client';
import { startTransition } from 'react';
import { useRouter } from 'next/navigation';
export default function ErrorBoundary({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const router = useRouter();
  function retry() { startTransition(() => { router.refresh(); reset(); }); }
  return <section className="card space-y-4"><h1 className="text-2xl font-bold">Topic temporarily unavailable</h1>
    <p role="alert">The server could not load this topic.</p>
    <button className="action" onClick={retry}>Try again</button>
  </section>;
}
```

The server page intentionally encounters a 503 and throws. Its segment boundary shows a generic message; a test verifies that the private diagnostic string does not appear in the production browser document. After the origin is repaired, the button requests fresh server rendering with router.refresh() and resets the boundary in a transition. A reset-only attempt retained the failed payload in this Next.js 14 experiment; resetting local error state and obtaining fresh server data are distinct operations. Do not confuse this retry with durable recovery of a transaction.

An error boundary applies to its segment's children; a failure in the same segment's layout needs a boundary above it, and the root layout has special global handling. Event-handler or API-request failures still need their own handling. Expected user validation errors should produce useful feedback instead of deliberately crashing rendering. [Error handling](https://nextjs.org/docs/14/app/building-your-application/routing/error-handling)

---

## 13. Node runtime, Edge runtime and middleware

### 13.1 Runtime is not deployment geography

The Node runtime supports Node APIs and typical server libraries. The Edge runtime offers a more constrained API surface; check each dependency rather than assuming that a Node database client or filesystem operation works there. Choosing Edge does not remove database distance, connection limits or authorization work. ISR is not available in the Edge runtime in the Next.js 14 model. [Edge and Node runtimes](https://nextjs.org/docs/14/app/building-your-application/rendering/edge-and-nodejs-runtimes)

The fixture's main handlers explicitly choose nodejs. Its Next.js 14 middleware is compiled/executed locally using the framework's middleware path. That verifies matching/header behavior, not placement near global users or a hosted Edge service.

### 13.2 Middleware is a request-routing layer

**middleware.ts**

```typescript
import { NextResponse } from 'next/server';

export function middleware() {
  const response = NextResponse.next();
  response.headers.set('x-m21-middleware', 'seen');
  return response;
}
export const config = { matcher: ['/dashboard/:path*'] };
```

The matcher covers dashboard routes. Those responses have x-m21-middleware: seen; the public topic API is outside the matcher and still executes. This is a useful counterexample to “my middleware protects every endpoint.” The middleware here performs no authentication.

Middleware is useful for light request decisions such as rewrites, redirects or routing metadata. Expensive data access and long jobs do not become cheap by moving them there. A real application should enforce permission at the trusted data/action boundary as well as any early routing check. [Next.js 14 middleware](https://nextjs.org/docs/14/app/building-your-application/routing/middleware)

**Resume answer:** explain what your middleware actually inspected, which paths matched, what it returned, its runtime restrictions and where authorization was enforced. “Used Edge Middleware” alone does not establish a secure or globally fast system.

---

## 14. Environment variables and server/client disclosure

Unprefixed variables belong to server code by default. NEXT_PUBLIC_ values are intended for browser exposure and are inlined during the build; changing a deployment environment value later does not necessarily change an already-built browser bundle. A public API base URL is different from a provider secret. [Next.js 14 environment variables](https://nextjs.org/docs/14/app/building-your-application/configuring/environment-variables)

This example's marker is deliberately synthetic. Keeping it out of source/browser output is observable, but replacing it with a secret and then returning that secret from a handler or passing it to client props would still disclose it. Review outputs, logs and serialization as well as import placement.

For a BFF, the browser can send a session cookie while the server uses a separately held provider credential. The two identities have different audiences and permissions. Do not forward every cookie, authorization header or upstream error body indiscriminately.

---

## 15. Tailwind: generated CSS utilities

Tailwind maps utility classes to CSS rules during the build. It is not a JavaScript UI framework, a substitute for semantic HTML, or a runtime authorization feature. Read a class sequence as normal CSS decisions: spacing, layout, typography, color and state.

The fixture uses Tailwind **3.4.19** through PostCSS:

**tailwind.config.cjs**

```javascript
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: { extend: {} }, plugins: [],
};
```

**postcss.config.cjs**

```javascript
module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

**app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .action { @apply rounded border border-blue-700 bg-blue-700 px-4 py-2 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700; }
  .card { @apply min-w-0 rounded-xl border border-slate-300 bg-white p-6 shadow-sm; }
}
```

The content paths must cover the files containing class names; otherwise valid-looking classes may have no generated rules. Keep complete class strings detectable, for example a fixed map of success/error classes. Constructing bg-${color}-700 from unrelated runtime fragments does not reliably expose the required full tokens to scanning. Only map approved values; do not treat a large safelist as a substitute for an understandable style design. [Tailwind 3 content configuration](https://v3.tailwindcss.com/docs/content-configuration), [PostCSS installation](https://v3.tailwindcss.com/docs/installation/using-postcss)

### 15.1 Mobile-first responsive behavior

The home cards use grid grid-cols-1 gap-6 md:grid-cols-2. Base rules apply at all widths; md changes the layout at that minimum-width breakpoint, rather than meaning “mobile devices only.” State variants such as focus-visible: and disabled: describe interaction states. [Tailwind 3 responsive design](https://v3.tailwindcss.com/docs/responsive-design)

Actual computed layouts:

```json
{
  "desktopColumns": "468px 468px",
  "mobileColumns": "358px",
  "widths": [
    1360,
    390
  ]
}
```

At 1360px the grid has two columns; at 390px it has one. The narrow page has no horizontal overflow, and both captured screenshots were visually inspected. These selected observations are not an exhaustive responsive or accessibility audit.

Use headings, labels, native buttons and meaningful focus styles regardless of utility syntax. The lookup's disabled state stops repeated submissions; its live status reports outcomes. CSS can visually hide or reorder content without changing permission or necessarily improving keyboard/screen-reader behavior.

### 15.2 Tailwind 4 is a separate setup

The handbook site uses Tailwind 4. Its CSS import/PostCSS integration differs from this v3 example, including the separate @tailwindcss/postcss package and CSS-first configuration. Do not paste a v3 installation block into a v4 project without checking its setup. Utility concepts transfer, but build configuration and some utilities changed. [Tailwind upgrade guide](https://tailwindcss.com/docs/upgrade-guide)

---

## 16. Architectural understanding: build a placement dashboard

### 16.1 Establish requirements first

Assume a real product needs public topics, a private progress dashboard, note edits and a long document import. Clarify who owns each note, whether users share an organization, when results must be fresh, whether drafts survive reload, and what import completion means. The fixture verifies selected mechanisms independently; it does not claim to implement this complete product.

| Feature | Suggested boundary | Reason to explain |
| --- | --- | --- |
| Public topic description | Prebuilt/revalidated server page | Reusable content with explicit freshness |
| Private progress overview | Session-aware server data access | Scope each record to verified identity |
| Editable note interaction | Small client form + authorized server mutation | UI feedback and trusted validation have different roles |
| Public browser lookup | Route Handler + minimal response contract | Browser-to-server boundary |
| Shared backend domain rules | Domain service called by server page/handler | Avoid duplicate rules and needless self-HTTP calls |
| Large import | Validated upload + durable job/status flow | Outlive an individual page request |

### 16.2 Read and write paths

```text
Public read:
URL -> route/layout -> cached public content -> HTML + client island

Private read:
request -> verify session -> scope data query -> render safe props

Note edit:
client form -> validate HTTP/body/origin/session
            -> authorize note ownership
            -> transaction / domain update
            -> invalidate appropriate public/private view policy
            -> return result and update or refresh affected UI

Import:
authorized upload -> validate/store -> durable enqueue
                 -> bounded worker -> idempotent result/status
                 -> dashboard polls/subscribes to authorized status
```

For an internal-only Next application, a Server Action can be another mutation interface. It is still a reachable server operation that needs input validation and permission checks. A Route Handler is useful for an explicit HTTP contract shared with other clients or integrations. Server Actions are covered conceptually here; the example does not execute them. [Next.js 14 Server Actions](https://nextjs.org/docs/14/app/building-your-application/data-fetching/server-actions-and-mutations)

### 16.3 Implementation order

1. Define route/data ownership and public versus private responses.
2. Build semantic static UI and the smallest useful client boundaries.
3. Implement shared server services with trusted authorization/query scope.
4. Define HTTP contracts and negative validation/permission tests.
5. Select explicit data and route cache policies with freshness requirements.
6. Add mutation invalidation and visible client update behavior.
7. Isolate slow sections and handle missing/failing dependencies.
8. Verify full loads, soft navigation, refresh, failure and narrow layouts.
9. Add operational tracing/timeouts/limits and deployment-specific checks.

### 16.4 Diagnose the common failures

**New data is absent after a save:** first establish that the write committed. Then inspect which data fetch, generated output or browser payload was reused. Name the exact invalidation/update operation; do not add random refresh calls until the symptom disappears.

**A layout draft disappears:** distinguish a sibling Link navigation from leaving the layout or reloading. Check key/type changes and the owner's lifetime before blaming the router.

**A hydration warning appears:** compare actual initial HTML and first client inputs. Check browser APIs, nondeterministic rendering, invalid markup and environment formatting.

**An API works despite a protected page:** a hidden link or unmatched middleware path did not authorize that direct HTTP request. Verify at the handler/service/data boundary.

**Tailwind classes do nothing:** check content coverage, complete tokens, global CSS import, compiled CSS, breakpoint width and cascade. A class present in source is not proof that its intended rule exists or wins.

### 16.5 Resume explanation ladder

In 30 seconds, explain Next as the framework around React routing/rendering/server endpoints. In two minutes, trace one public or private page and its client boundary. In five minutes, add the API/data ownership, cache policy, mutation refresh and one failure test.

For your actual project, distinguish what you implemented from framework behavior you relied on. Quote only measured results you can support. This fixture does not establish your project's routing system, deployment platform, performance gains or permission model.

---

## 17. Next.js 14 versus newer releases

| Area | Next.js 14 context here | Newer-version difference to verify |
| --- | --- | --- |
| Request APIs | Synchronous cookies()/headers(), ordinary params object | Next 15 introduced async request APIs; later code awaits promises |
| fetch / GET handlers | More cache-oriented defaults, with context-dependent opt-outs | Next 15 changed fetch and GET handler defaults to uncached |
| Client navigation cache | Page payload reuse follows v14 rules | Next 15 changed page segment defaults; layouts still have reuse behavior |
| Middleware | middleware.ts with Edge restrictions | Next 16 deprecated the name in favor of proxy.ts; Proxy has a different runtime contract |
| Tag invalidation | revalidateTag(tag) in the tested example | Next 16 recommends the cache-life profile form and has other mutation APIs |
| Build tool | v14 fixture runs its installed next build | v16 defaults differ; the handbook uses an explicit webpack build |
| Tailwind | v3 content configuration and @tailwind directives | v4 has a different integration/configuration model |

These are migration landmarks, not code executed by this fixture. Consult [Next 15 upgrade guidance](https://nextjs.org/docs/app/guides/upgrading/version-15), [Next 16 upgrade guidance](https://nextjs.org/docs/app/guides/upgrading/version-16) and the installed project's docs before editing a newer application. Do not rename Edge middleware to Proxy without reviewing the runtime change.

---

## 18. Must remember and common wrong answers

| Say this | Avoid this |
| --- | --- |
| Identify version and router first | Every Next example uses the same signature/default |
| Client Components can have initial server HTML | use client disables all server rendering |
| Server output/props can disclose data | Server Component means its output is secret |
| Dynamic path names and render timing are separate | A [slug] page must be SSR |
| Layout state follows component lifetime | Layout memory persists across all reloads/devices |
| Name the specific cache and invalidation | router.refresh clears all server caches |
| HTTP/API input needs runtime validation | TypeScript validates request.json automatically |
| Middleware matching is one early layer | A protected page protects every API |
| Echo field length differs from ingress body size | An 80-character field limit bounds network payload parsing |
| ISR permits traffic-driven refreshing | revalidate=1 is a strict one-second cron |
| Tailwind compiles CSS and needs detectable tokens | Any dynamically assembled class automatically exists |
| Tests establish selected local mechanisms | A local run proves hosted Edge/CDN or production security |

---

## 19. Interview questions and follow-ups

### Q1. What is Next.js, and why use it with React?

It supplies application routing, rendering/build conventions and server interfaces around React. Explain which of those your application needed and the extra runtime/cache decisions they introduce.

### Q2. React, Next.js and Tailwind: what does each do?

React describes UI, Next organizes and serves the application, and Tailwind generates CSS utilities. Neither styling nor client routing authorizes access to server records.

### Q3. App Router versus Pages Router?

Identify app/ versus pages/. Their page/layout and endpoint conventions differ; the fixture runs App pages/handlers alongside a separate Pages API URL.

### Q4. How does a folder become a route?

A page file exposes UI and a route file exposes a handler. [slug] captures input; a parenthesized route group organizes files without adding its name to the path.

### Q5. Layout versus template?

A shared layout can preserve mounted state across matching navigation. A template remounts. The test's shared counter survives Settings navigation but resets on full reload.

### Q6. Does a dynamic URL segment imply SSR?

No. The catalog's two slug values are generated at build time. Request-dependent data is a different decision from URL parameter syntax.

### Q7. What is a Server Component?

An App Router server-rendered component implementation that can perform server data work without shipping that implementation as a client component. It does not imply every render happens on each request.

### Q8. What does use client mean?

It creates a client module boundary for capabilities such as state and handlers. Initial full loads can still include server HTML for those components.

### Q9. Can a Server Component render a Client Component?

Yes; the home page renders a counter island. Pass safe React-serializable values. Do not pass credentials just because the caller runs on the server.

### Q10. What is hydration?

React makes supplied HTML interactive using client code and matching initial inputs. The no-JS experiment can read the page but cannot use the React counter handler.

### Q11. Why does hydration mismatch happen?

The initial browser result differs from supplied markup. Investigate browser-only reads, nondeterministic values, invalid HTML and formatting before suppressing the warning.

### Q12. CSR, SSR, SSG and ISR?

They describe browser rendering, request-time HTML, reusable build output and refreshable reusable output. A static page can also contain an interactive hydrated island.

### Q13. Why call a service directly from a Server Component?

If the same server owns that service, a self-HTTP call adds an unnecessary boundary. The browser still needs an endpoint to reach server-only data.

### Q14. Route Handler versus Pages API route?

App handlers export named methods using Web Request/Response. Pages API routes export a default request/response handler. Both run real HTTP contracts in this example.

### Q15. Does TypeScript validate the POST body?

No. Parse network data and validate runtime shape. The shared contract rejects missing/wrong/extra fields and out-of-range strings.

### Q16. Why distinguish 400, 415 and 422 here?

They identify malformed JSON, unsupported media type and parsed-but-invalid data in this contract. Consistent documented behavior matters more than copying one status table blindly.

### Q17. Does a field length limit prevent oversized payload parsing?

No. The App echo checks the parsed string. The Pages example separately configures a 1kb parser limit, and its oversized-body test returns 413.

### Q18. What are the four Next.js 14 cache layers?

Render request memoization, server Data Cache, generated Full Route Cache and browser Router Cache. State the reused object and lifetime before choosing an invalidation.

### Q19. Does no-store mean duplicate GETs cannot be deduplicated?

No. In the component render experiment, identical live reads reach the origin once per render, then refetch on the next request. Persistent reuse and render deduplication differ.

### Q20. Why might router.refresh still show stale data?

New rendering can reuse persistent cached server data. Establish whether the write committed, then invalidate the right data/path and update the browser appropriately.

### Q21. revalidateTag versus revalidatePath?

They select tagged data versus a path/layout scope. In the tested v14 handler, tag invalidation leads the next visit to refetch. Neither is a database write or a broadcast to every open tab.

### Q22. Is ISR a periodic background job?

No. Expiration and subsequent access drive refresh. The verifier waits for eventual updated output; it does not claim exact one-second availability.

### Q23. What does streaming solve?

It lets ready UI arrive while a bounded section waits. The controlled origin test sees the fallback before releasing the dependency and the resolved section afterwards.

### Q24. What does an error boundary recover?

Its covered rendering subtree. The fixture repairs a dependency, refreshes the server payload and resets the boundary. Event-handler/API failures and transaction recovery require their own handling.

### Q25. Node versus Edge runtime?

Check available APIs, package compatibility and data location. Local middleware behavior does not prove global execution or lower end-to-end latency.

### Q26. Does middleware secure every API?

Only matched requests encounter it, and an early check is not the whole permission boundary. The fixture's dashboard matcher does not cover its public API.

### Q27. Why avoid NEXT_PUBLIC_ for a secret?

That prefix intentionally exposes a build-inlined value to the browser. A server variable can also leak if returned or serialized, so inspect data flows as well as names.

### Q28. Why can a Tailwind class appear in source but do nothing?

The file/token may not be scanned, the integration/import may be wrong, or another rule/breakpoint may win. Check actual generated and computed CSS.

### Q29. What does md:grid-cols-2 mean?

At the md minimum width, use two grid columns; the base grid-cols-1 remains the narrow layout. It is a viewport rule, not device detection.

### Q30. Design a Next.js placement dashboard in five minutes.

Separate public reusable topics from authenticated progress, choose server data owners and small client islands, define mutation contracts/authorization, then explain cache invalidation and visible refresh. Add loading/failure/navigation tests and a durable job path for imports. State the exact Next/Tailwind versions.

---

## 20. Practice tasks

1. **Draw the route tree.** Map every example URL to its file and distinguish App/Pages interfaces.
2. **Trace a full load.** Explain HTML preview, RSC information, client code and hydration using the no-JS comparison.
3. **Predict state lifetime.** Compare sibling Link navigation, leaving a layout and full reload.
4. **Separate route syntax from rendering.** Inspect the prerender manifest and compare public slug stamps with cookie dashboard stamps.
5. **Break both API contracts.** Send malformed JSON, wrong media type/data, unsupported methods and an oversized Pages body.
6. **Observe actual cache calls.** Predict the duplicate reads and successive origin versions before running the cache lab.
7. **Invalidate deliberately.** Reject an unauthenticated fixture control, invalidate the fixed public tag and verify the next read.
8. **Test partial failure.** Hold/release the streaming dependency, then repair/reset the failing segment; distinguish loading, missing and error states.
9. **Inspect compiled CSS.** Verify one/two columns and trace a deliberately omitted class back to content scanning or cascade.
10. **Defend an architecture.** Design private notes plus durable imports, then list the v14-to-newer-version changes you must check.

---

## 21. Exit checklist

- [ ] I can distinguish React, Next.js, Tailwind and TypeScript.
- [ ] I can identify App/Pages routing and map files to URLs.
- [ ] I can predict layout state across navigation and reload.
- [ ] I can explain Server/Client boundaries without claiming client means no server HTML.
- [ ] I can trace initial HTML, hydration and subsequent navigation.
- [ ] I can separate dynamic paths, SSR, SSG, ISR and streaming.
- [ ] I can implement and validate both endpoint interfaces.
- [ ] I can explain direct server data access versus a browser/BFF request.
- [ ] I can name cache owners and justify invalidation/freshness.
- [ ] I can handle loading, missing resources, server failure and retry.
- [ ] I can explain runtime/middleware/secret boundaries and their limits.
- [ ] I can verify Tailwind output and distinguish v14/v3 setup from newer versions.

These learning checks stay unchecked until you can demonstrate them.

---

## 22. Sources and verification map

Primary references are linked beside the concepts. Additional baseline material: [Next.js 14 installation](https://nextjs.org/docs/14/getting-started/installation), [React hydration](https://react.dev/reference/react-dom/client/hydrateRoot), [Next.js 14 useRouter](https://nextjs.org/docs/14/app/api-reference/functions/use-router) and [fetching/revalidation](https://nextjs.org/docs/14/app/building-your-application/data-fetching/fetching-caching-and-revalidating). Version migration material is conceptual comparison, not a second executed framework fixture.

**54 actual checks passed:**

| Group | Checks |
| --- | --- |
| api | 11 |
| boundary | 3 |
| browser | 1 |
| browser_api | 2 |
| build | 4 |
| cache | 7 |
| errors | 2 |
| hydration | 3 |
| middleware | 2 |
| pages_api | 5 |
| rendering | 5 |
| routing | 4 |
| streaming | 2 |
| tailwind | 3 |
| **Total** | **54** |

All named checks and observations are recorded in examples/resume-skills/module-21-nextjs/verification-results.json and verification-output.txt. fixture-build-output.txt contains the real framework build/type/prerender output. fixture-server-output.txt includes the expected deliberate dependency failure; that server log is not evidence of an unhandled browser exception.

origin.mjs supplies counted/versioned/held/failing local responses. verify.mjs owns the build/server/browser lifecycle. The chapter embeds the relevant components, data/contract modules, routes, cache/ISR/streaming examples, middleware and Tailwind configuration exactly. Browser screenshots were captured and visually inspected. cleanup-results.json records closure; dependency-audit.json records the historical package risk without hiding the findings. Content/site/summary validation artifacts verify integration separately from the fixture.

No real authentication/database, durable mutation, Server Action run, hosted Edge/CDN behavior, production deployment, comprehensive assistive-technology audit or performance benchmark was executed. Selected local checks establish the demonstrated mechanisms only.

---

## Next

Continue to [M22: LLM and AI API Fundamentals](/docs/resume-skills/llm-ai-api-fundamentals) for tokens/context, prompts, inference, streaming, structured outputs, tools, provider boundaries, retries, cost and evaluation.

Revisit [M20: React](/docs/resume-skills/react-fundamentals) for state/effects/identity, [M7: Authentication](/docs/resume-skills/authentication-sessions-jwt-oauth) and [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) for trusted private data, [M15: Durable jobs](/docs/resume-skills/caching-background-jobs-data-ingestion) for imports, and the [master roadmap](/docs/resume-skills) for the remaining track.
