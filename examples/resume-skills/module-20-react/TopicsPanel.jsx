import { useState } from 'react';
import { fetchIgnoringAbort, fetchTopics, useTopics } from './useTopics.js';
import { record } from './diagnostics.js';

export function TopicsPanel() {
  const [draft, setDraft] = useState(''), [query, setQuery] = useState('');
  const ignoreAbort = new URLSearchParams(window.location.search).get('ignoreAbort') === '1';
  const state = useTopics(query, ignoreAbort ? fetchIgnoringAbort : fetchTopics, record);
  return <div>
    <form onSubmit={event => { event.preventDefault(); setQuery(draft.trim()); }}>
      <label htmlFor="topic-query">Topic query</label>
      <input id="topic-query" value={draft} onChange={event => setDraft(event.target.value)} />
      <button type="submit">Search topics</button>
    </form>
    <div aria-live="polite" aria-busy={state.status === 'loading'}>
      {state.status === 'idle' && <p role="status">Enter a query.</p>}
      {state.status === 'loading' && <p role="status">Loading topics…</p>}
      {state.status === 'error' && <><p role="alert">Could not load topics.</p><button onClick={state.retry}>Retry topics</button></>}
      {state.status === 'success' && (state.items.length ? <ul aria-label="Topic results">{state.items.map(item => <li key={item.id}>{item.title}</li>)}</ul> : <p role="status">No topics found.</p>)}
    </div>
  </div>;
}
