import { useRef, useState } from 'react';
import { record } from './diagnostics.js';

export function SnapshotCounter() {
  const [count, setCount] = useState(0);
  const [captured, setCaptured] = useState('none');
  const callback = useRef(null);
  function replacements() {
    const before = count;
    setCount(count + 1); setCount(count + 1); setCount(count + 1);
    record('snapshot', { before, afterInHandler: count });
  }
  return <section aria-labelledby="counter-title">
    <h2 id="counter-title">State snapshots</h2>
    <p>Count: <output data-testid="count">{count}</output></p>
    <div className="actions">
      <button onClick={replacements}>Three replacements</button>
      <button onClick={() => { setCount(n => n + 1); setCount(n => n + 1); setCount(n => n + 1); }}>Three updaters</button>
      <button onClick={() => setCount(0)}>Reset count</button>
      <button onClick={() => { callback.current = () => setCaptured(count); }}>Capture callback</button>
      <button onClick={() => callback.current?.()}>Run captured callback</button>
    </div>
    <p>Captured: <output data-testid="captured">{captured}</output></p>
  </section>;
}

export function RefAndObjectLab() {
  const counter = useRef(0), input = useRef(null);
  const [published, setPublished] = useState(0);
  const [profile, setProfile] = useState({ name: 'Rupam', preferences: { theme: 'light' } });
  function updateTheme() {
    const next = { ...profile, preferences: { ...profile.preferences, theme: 'dark' } };
    record('immutable-update', { previousTheme: profile.preferences.theme, sameObject: next === profile, sameNested: next.preferences === profile.preferences });
    setProfile(next);
  }
  return <section aria-labelledby="ref-title">
    <h2 id="ref-title">Refs and immutable updates</h2>
    <p>Published ref: <output data-testid="published-ref">{published}</output></p>
    <div className="actions">
      <button onClick={() => { counter.current++; }}>Increment ref</button>
      <button onClick={() => setPublished(counter.current)}>Publish ref</button>
      <button onClick={updateTheme}>Update nested theme</button>
    </div>
    <p data-testid="profile">{profile.name}: {profile.preferences.theme}</p>
    <label htmlFor="focus-target">Focus target</label>
    <input id="focus-target" ref={input} />
    <button onClick={() => input.current?.focus()}>Focus input</button>
  </section>;
}
