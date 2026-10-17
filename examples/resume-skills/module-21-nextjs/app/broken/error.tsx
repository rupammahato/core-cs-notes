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
