import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { SnapshotCounter, RefAndObjectLab } from './StateLab.jsx';
import { IdentityLab } from './IdentityLab.jsx';
import { EffectsLab } from './EffectsLab.jsx';
import { FormsLab } from './FormsLab.jsx';
import { TopicsPanel } from './TopicsPanel.jsx';
import { ContextLab } from './ContextLab.jsx';
import { events, subscriptions } from './diagnostics.js';

function App() {
  const [topicsMounted, setTopicsMounted] = useState(true);
  return <main>
    <header><p className="eyebrow">Placement handbook · M20</p><h1>React fundamentals lab</h1>
      <p>Small experiments for snapshots, identity, effects and a real HTTP boundary.</p></header>
    <div className="grid">
      <SnapshotCounter /><RefAndObjectLab /><IdentityLab /><EffectsLab /><FormsLab />
      <section aria-labelledby="topics-title"><h2 id="topics-title">API state and cleanup</h2>
        <p>Queries: node, empty, error, malformed, html, slow, fast.</p>
        <button onClick={() => fetch('/fixture/release-slow', { method: 'POST' })}>Release held API reply</button>
        <button onClick={() => fetch('/fixture/recover', { method: 'POST' })}>Recover fixture API</button>
        <button onClick={() => setTopicsMounted(value => !value)}>{topicsMounted ? 'Unmount topic panel' : 'Mount topic panel'}</button>
        {topicsMounted && <TopicsPanel />}
      </section>
      <ContextLab />
    </div>
  </main>;
}
const root = createRoot(document.getElementById('root'));
const strict = new URLSearchParams(window.location.search).get('strict') === '1';
root.render(strict ? <StrictMode><App /></StrictMode> : <App />);
window.M20 = { events, activeSubscriptions: () => subscriptions.size, unmount: () => root.unmount() };
