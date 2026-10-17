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
