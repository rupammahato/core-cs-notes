import { createContext, memo, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { record } from './diagnostics.js';
const Theme = createContext('light');
function ThemeLabel() { return <p data-testid="context-theme">Theme: {useContext(Theme)}</p>; }
const MemoChild = memo(function MemoChild({ label, onPick }) {
  useEffect(() => { record('memo-child-commit', { label }); });
  return <button onClick={onPick}>Pick {label}</button>;
});
export function ContextLab() {
  const [theme, setTheme] = useState('light'), [tick, setTick] = useState(0);
  const [label, setLabel] = useState('React'), [picked, setPicked] = useState(0);
  const onPick = useCallback(() => setPicked(value => value + 1), []);
  const description = useMemo(() => label.toUpperCase(), [label]);
  return <section aria-labelledby="context-title">
    <h2 id="context-title">Context and memoization</h2>
    <Theme.Provider value={theme}><ThemeLabel /></Theme.Provider>
    <button onClick={() => setTheme(value => value === 'light' ? 'dark' : 'light')}>Toggle context theme</button>
    <button onClick={() => setTick(n => n + 1)}>Memo parent update</button>
    <span>Parent updates: {tick}</span>
    <button onClick={() => setLabel(value => value === 'React' ? 'Node' : 'React')}>Change memo prop</button>
    <MemoChild label={label} onPick={onPick} />
    <p data-testid="picked">Picked: {picked}</p><p data-testid="memo-derived">Derived: {description}</p>
  </section>;
}
