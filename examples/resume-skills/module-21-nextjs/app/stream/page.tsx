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
