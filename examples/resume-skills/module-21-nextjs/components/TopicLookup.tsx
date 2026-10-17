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
