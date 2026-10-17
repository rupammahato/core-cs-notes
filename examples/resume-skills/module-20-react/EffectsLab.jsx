import { useEffect, useState } from 'react';
import { record, subscriptions } from './diagnostics.js';

function Subscription({ topic }) {
  useEffect(() => {
    const subscription = { topic };
    subscriptions.add(subscription); record('subscription-setup', { topic });
    return () => { subscriptions.delete(subscription); record('subscription-cleanup', { topic }); };
  }, [topic]);
  return <p>Subscribed to: {topic}</p>;
}
export function EffectsLab() {
  const [topic, setTopic] = useState('react');
  const [mounted, setMounted] = useState(true);
  const [tick, setTick] = useState(0);
  return <section aria-labelledby="effects-title">
    <h2 id="effects-title">Effect lifecycle</h2>
    <label htmlFor="effect-topic">Subscription topic</label>
    <select id="effect-topic" value={topic} onChange={event => setTopic(event.target.value)}>
      <option value="react">react</option><option value="node">node</option>
    </select>
    <button onClick={() => setTick(n => n + 1)}>Same dependency update</button>
    <span>Local updates: {tick}</span>
    <button onClick={() => setMounted(value => !value)}>{mounted ? 'Unmount subscription' : 'Mount subscription'}</button>
    {mounted && <Subscription topic={topic} />}
  </section>;
}
