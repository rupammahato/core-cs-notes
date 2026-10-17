import { useState } from 'react';
const subjects = ['React', 'Node.js', 'PostgreSQL'];

export function FormsLab() {
  const [name, setName] = useState(''), [error, setError] = useState(''), [saved, setSaved] = useState('');
  const [filter, setFilter] = useState(''), [onlyReact, setOnlyReact] = useState(false);
  const visible = subjects.filter(subject => subject.toLowerCase().includes(filter.toLowerCase()) && (!onlyReact || subject === 'React'));
  function submit(event) {
    event.preventDefault();
    if (!name.trim()) { setError('Enter a display name.'); setSaved(''); return; }
    setError(''); setSaved(name.trim());
  }
  return <section aria-labelledby="forms-title">
    <h2 id="forms-title">Controlled forms and derived data</h2>
    <form onSubmit={submit} noValidate>
      <label htmlFor="display-name">Display name</label>
      <input id="display-name" value={name} aria-invalid={Boolean(error)} aria-describedby={error ? 'name-error' : undefined} onChange={event => setName(event.target.value)} />
      <button type="submit">Save name</button>
      {error && <p id="name-error" role="alert">{error}</p>}
      {saved && <p role="status">Saved: {saved}</p>}
    </form>
    <label htmlFor="subject-filter">Filter subjects</label>
    <input id="subject-filter" value={filter} onChange={event => setFilter(event.target.value)} />
    <label><input type="checkbox" checked={onlyReact} onChange={event => setOnlyReact(event.target.checked)} /> React only</label>
    <p data-testid="subject-count">{visible.length} visible</p>
    <ul aria-label="Filtered subjects">{visible.map(subject => <li key={subject}>{subject}</li>)}</ul>
  </section>;
}
