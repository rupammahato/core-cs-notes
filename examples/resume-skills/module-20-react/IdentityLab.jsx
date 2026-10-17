import { useState } from 'react';

const initial = [{ id: 'a', label: 'Alpha' }, { id: 'b', label: 'Beta' }];
function Row({ item, mode }) {
  const [draft, setDraft] = useState(item.label);
  const id = 'draft-' + mode + '-' + item.id;
  return <li data-item-id={item.id}>
    <label htmlFor={id}>{item.label} draft</label>
    <input id={id} value={draft} onChange={event => setDraft(event.target.value)} />
  </li>;
}
function Rows({ mode }) {
  const [items, setItems] = useState(initial);
  return <>
    <button onClick={() => setItems(items => [...items].reverse())}>Reverse rows</button>
    <ul>{items.map((item, index) => <Row key={mode === 'stable' ? item.id : index} item={item} mode={mode} />)}</ul>
  </>;
}
function Editor({ person }) {
  const [note, setNote] = useState('');
  return <><label htmlFor="person-note">{person} note</label><input id="person-note" value={note} onChange={event => setNote(event.target.value)} /></>;
}
export function IdentityLab() {
  const [mode, setMode] = useState('stable');
  const [person, setPerson] = useState('Ada');
  const [tick, setTick] = useState(0);
  return <section aria-labelledby="identity-title">
    <h2 id="identity-title">Identity and keys</h2>
    <label htmlFor="key-mode">Key strategy</label>
    <select id="key-mode" value={mode} onChange={event => setMode(event.target.value)}>
      <option value="stable">Stable item IDs</option><option value="index">Index counterexample</option>
    </select>
    <Rows key={mode} mode={mode} />
    <hr />
    <button onClick={() => setTick(n => n + 1)}>Unrelated parent update</button>
    <span>Parent updates: {tick}</span>
    <button onClick={() => setPerson(person === 'Ada' ? 'Lin' : 'Ada')}>Switch person</button>
    <Editor key={person} person={person} />
  </section>;
}
