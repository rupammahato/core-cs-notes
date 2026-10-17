import { useEffect, useState } from 'react';
const noop = () => {};

export async function fetchTopics(query, { signal } = {}) {
  const response = await fetch('/api/topics?q=' + encodeURIComponent(query), { signal });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const data = await response.json();
  if (!Array.isArray(data.items) || data.items.length > 20 || data.items.some(item =>
    !item || typeof item.id !== 'string' || !item.id || typeof item.title !== 'string' || item.title.length > 100)
    || new Set(data.items.map(item => item.id)).size !== data.items.length) {
    throw new Error('Invalid topic response');
  }
  return data.items;
}

// Only used by the race experiment: transport completes despite cleanup abort.
export function fetchIgnoringAbort(query) { return fetchTopics(query); }

export function useTopics(query, loader = fetchTopics, onEvent = noop) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState({ query: '', status: 'idle', items: [] });
  useEffect(() => {
    if (!query) { setState({ query, status: 'idle', items: [] }); return; }
    let active = true;
    const controller = new AbortController();
    setState({ query, status: 'loading', items: [] });
    onEvent('request-start', { query });
    loader(query, { signal: controller.signal }).then(items => {
      if (!active) { onEvent('ignored-result', { query }); return; }
      setState({ query, status: 'success', items });
      onEvent('request-success', { query });
    }).catch(error => {
      if (!active || error.name === 'AbortError') { onEvent('ignored-error', { query }); return; }
      setState({ query, status: 'error', items: [] });
      onEvent('request-error', { query });
    });
    return () => {
      active = false; controller.abort(); onEvent('request-cleanup', { query });
    };
  }, [query, revision, loader, onEvent]);
  const visible = state.query === query ? state : { query, status: query ? 'loading' : 'idle', items: [] };
  return { ...visible, retry: () => setRevision(value => value + 1) };
}
