# Resume Skills Placement Handbook — Part 22
# Module 20: React Fundamentals

**Estimated time: 5–6 hours | Tier: 2 | Requires: M1 JavaScript, M2 async/closures, M3 TypeScript concepts; M6 HTTP for API examples**

---

## Why this module exists

A full-stack interview can move from your API to the screen that uses it. You should be able to explain what React is, why changing a variable does not necessarily update the screen, how components share data, why an effect reconnects, and how a late response can put the wrong result into the UI.

This chapter builds that explanation from components and state through identity, effects, forms and a small API-driven screen. It covers selected resume-linked fundamentals and useful follow-ups, not a measured ranking of company interview frequency. Next.js rendering/routing and Tailwind follow in M21.

**Organizing principle: describe the UI for the current inputs, give each piece of state a deliberate owner, and synchronize external work with an explicit lifecycle.**

---

## 1. What React is and where it sits

React is a library for building user interfaces from components. A component describes UI using inputs such as props, state and context. React DOM is the renderer that connects React's description to the browser DOM. JavaScript is the language; the browser supplies DOM, events, networking and paint. A framework can add routing, server rendering and other application conventions.

```text
User event / external result
   -> state update at its owner
   -> React calculates the next UI description
   -> renderer commits necessary DOM changes
   -> browser performs layout/paint as needed

Browser fetch -> HTTP API -> backend authorization/business logic/storage
```

React helps keep a changing UI consistent with its state. It does not replace backend authorization, HTTP semantics, a database or careful HTML/CSS. A hidden button is not an ownership check; client-side validation is not a trusted API boundary.

Revisit [M1](/docs/resume-skills/javascript-fundamentals) for objects/closures and [M2](/docs/resume-skills/asynchronous-javascript) for asynchronous outcomes. The effect/race examples are applications of those JavaScript mechanisms.

---

## 2. What was actually verified

**Recorded on 15 October 2026:** Node v22.14.0 on Windows, using an installed headless Chrome browser.

| Runtime/library | Recorded version |
| --- | --- |
| Node | v22.14.0 |
| react | 19.3.1 |
| react-dom | 19.3.1 |
| esbuild | 0.28.2 |
| playwright-core | 1.64.1 |
| Chrome | 155.0.8059.40 |

The independent fixture uses React 19.3.1. The handbook website has its own dependency tree; its installed React/Next versions are a separate context and were not upgraded for this chapter. esbuild transforms JSX and makes separate development/production browser bundles. React Compiler is not enabled.

### Reproduce the browser checks

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-20-react
npm ci
npm run build
npm run verify
```

The verifier uses playwright-core with an installed Chromium-based browser. It searches the recorded Chrome/Edge installation paths; set M20_BROWSER to another compatible executable path if needed. Initial package installation needs registry access. The test run itself uses owned local pages and HTTP endpoints.

For manual practice:

```powershell
npm run demo
```

The command prints an ephemeral loopback URL. Ctrl+C stops the manual server. Add ?strict=1 for root development Strict Mode, or ?strict=1&production=1 for the production bundle comparison. The manual command is intentionally started only when you run it; authoring left no server listening.

The browser suite starts an owned ephemeral server, opens its own headless browser, exercises DOM/keyboard/network behavior, saves screenshots and closes both. Port 3000 is unused and Docker is not started. The npm audit recorded zero reported vulnerabilities for this snapshot, without establishing overall application security.

### Evidence limits

These are actual browser DOM and local HTTP checks, not simulated component outputs. They do not establish assistive-technology compatibility across screen readers, every browser, production performance, real user authentication, backend durability, SSR/hydration or Next.js behavior. The local fixture controls held/error responses explicitly so races can be tested without a fragile timed sleep.

---

## 3. Components, JSX, props and composition

A function component returns a UI description. Use a capitalized component name in JSX so it is treated as a component rather than an ordinary HTML tag. Break a screen into parts that have a useful responsibility: a search form, status area, results list and editable row are natural examples.

**JSX** is syntax transformed into JavaScript element descriptions; it is not an HTML string sent directly to the browser. Expressions appear in braces, attributes follow JSX conventions such as className, and returned markup must form a valid expression, often one parent element or a fragment. JSX transformation is different from React Compiler's performance optimizations. [Writing JSX](https://react.dev/learn/writing-markup-with-jsx)

**Props** are inputs passed from a parent. Treat them as read-only snapshots. A callback prop lets a child request an action from the owner; it does not mutate the parent's variable by magic. children supports composition of nested content. [Passing props](https://react.dev/learn/passing-props-to-a-component)

```text
SearchScreen owns query
  +-- SearchForm receives value + onChange/onSubmit
  +-- Status receives loading/error/empty information
  +-- Results receives items
       +-- TopicRow receives one item
```

Conditional rendering is JavaScript choosing an element description. Lists commonly map data to elements. Use actual booleans for conditional expressions where a numeric zero would otherwise appear as text. Event handlers are functions passed to event props; calling a state-setting handler while rendering can create repeated renders instead of waiting for an event.

The fixture's components are defined at module scope. Defining a new component function inside a parent's render can give it a new type identity and unexpectedly reset state. Prefer deliberate component boundaries rather than nesting definitions to shorten a file.

---

## 4. Trigger, render, commit and paint

**Trigger:** initial mounting or an update requests work. **Render:** React calls components to calculate the next description. **Commit:** the renderer applies the required changes. **Paint:** the browser displays the result. A component function running does not imply every DOM node was recreated. [Render and commit](https://react.dev/learn/render-and-commit)

Rendering should be pure: compute from inputs without mutating existing external data, sending a request or starting a subscription. React can call rendering logic more than once, and work that begins rendering need not necessarily become a committed UI. Keep user actions in handlers and external synchronization in an appropriate lifecycle. [Keeping components pure](https://react.dev/learn/keeping-components-pure)

The key experiment verifies an existing input DOM node survives a reorder when logical identity is stable. This is a specific observable reuse result, not a complete reconstruction of React's internal scheduling/diff algorithm.

An effect runs in relation to a commit, not as part of a pure render calculation. Avoid the slogan useEffect always runs after paint: interaction-related timing can differ. useLayoutEffect is a specialized tool for work that must happen before paint; it can block paint and is not the default place for fetching data.

---

## 5. State is a render snapshot

useState gives a render its current state value and a setter that requests an update. Setting state does not rewrite the local variable in the already-running handler. Event handlers and callbacks close over the values from their render. [State as a snapshot](https://react.dev/learn/state-as-a-snapshot)

The counter begins at zero. Its Three replacements button executes setCount(count + 1) three times. All three use the same captured count, so the observed next count is one. Its Three updaters button applies three pure functions to the queued previous values, yielding three increments. [Queued updates](https://react.dev/learn/queueing-a-series-of-state-updates)

```jsx
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
```

Actual handler observation:

```json
{
  "type": "snapshot",
  "before": 0,
  "afterInHandler": 0
}
```

The DOM later shows the updated count, while before and afterInHandler both remain zero. Awaiting a state setter is not a reliable way to turn it into a promise for a new render snapshot. When the next value depends on the previous one, a functional updater communicates that relationship directly. Updaters must be pure; development checks can call them more than once.

### 5.1 Stored closures and stale values

The fixture stores a callback while count is zero, changes count to three, then executes the stored callback. It publishes captured zero. This is ordinary closure behavior, not a random React failure. A delayed callback, interval or event listener can similarly retain the values it captured.

Decide what the operation means: the value at scheduling time, the next state derived from previous state, or the latest external/ref value. Use the appropriate dependency/updater/ref design. Do not add refs to every variable merely to hide stale-state symptoms.

### 5.2 Object identity and immutable updates

State can hold objects/arrays, but mutation of existing state does not create the intended new snapshot. Copy the changed object and affected nested paths. A spread copies one level; it does not deeply clone the entire graph. Arrays can be updated through non-mutating transformations such as map/filter or a copied reverse.

Actual nested update:

```json
{
  "type": "immutable-update",
  "previousTheme": "light",
  "sameObject": false,
  "sameNested": false
}
```

The old theme remained light, while both outer and preferences references changed and the new UI showed dark. Copying every unrelated object is unnecessary; mutating shared nested state is unsafe. [Updating objects](https://react.dev/learn/updating-objects-in-state)

---

## 6. State ownership, derived data and lifting state

Store the minimal changing information needed to describe the screen. If filtered items or a count can be calculated from existing items/filter state, derive them during rendering instead of maintaining a second synchronized state variable through an effect.

When siblings must agree, their closest useful common owner can hold the state and pass values/callbacks down. This is lifting state up. It preserves one source of truth instead of keeping independent copies that must be repaired later. [Sharing state](https://react.dev/learn/sharing-state-between-components), [Thinking in React](https://react.dev/learn/thinking-in-react)

In FormsLab, the input and checkbox own source state in their parent; the filtered list and sibling count are derived from it. Filtering node shows Node.js and one visible item. Adding React only makes the derived result empty. No effect is required to synchronize the count with the list.

A custom hook shares reusable logic, not automatically one global state instance. Two calls to a stateful hook can have independent state. To share one result, choose an owner, context or an appropriate external/cache design rather than assuming the hook name creates singleton storage.

---

## 7. Hooks and refs

The state/effect/context/ref hooks in this chapter must be called consistently at the top level of a component or custom hook, rather than inside an event handler, conditional or loop. Put a condition inside the effect/handler or extract a component when needed. React relies on the hook structure to associate state with its owner. [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)

The newer use API has its own documented conditional/loop behavior; that is not permission to call useState/useEffect conditionally. Suspense/resource APIs and framework integration are outside this introductory fixture. [React use reference](https://react.dev/reference/react/use)

### 7.1 State versus ref

| Need | Common tool | Why |
| --- | --- | --- |
| A value changes what should be rendered | State | Updating it requests a new UI snapshot |
| Keep an imperative handle or non-rendered mutable value | Ref | current can persist without requesting a render |
| Synchronize with an external system | Effect and cleanup | Lifetime is explicit relative to committed inputs |
| Calculate a value from current inputs | Ordinary rendering calculation | No independent synchronization required |

A ref object persists across renders; changing current does not itself request a render. Avoid reading/writing mutable refs as ordinary render-time data. In the fixture, Increment ref changes a private counter, and Publish ref reads it in an event handler and sets displayed state. The focus button uses a DOM ref to focus the named input. [useRef](https://react.dev/reference/react/useRef)

Refs are useful escape hatches, not replacements for all state. Mutating a DOM node behind React's ownership can create inconsistencies; use refs for deliberate imperative operations that fit the component's design.

---

## 8. Identity, reconciliation and keys

React preserves state according to identity in the rendered tree: component type, position and relevant keys matter. A key lets siblings express logical identity when items move. Keys must be stable and unique among those siblings; they do not need to be globally unique. key is special metadata, so pass an explicit id prop when a child needs the ID itself. [Rendering lists](https://react.dev/learn/rendering-lists)

```jsx
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
```

### 8.1 The reorder experiment

With stable IDs, editing Alpha and reversing the rows kept Alpha edited with Alpha and reused that input's DOM node. With index keys, local draft state stayed at the position while item props changed:

```json
{
  "alpha": "Beta",
  "beta": "Alpha edited"
}
```

The row now labelled Beta received Alpha's edited draft. That is why index keys are troublesome for reorderable stateful lists. A truly static list without insertion/reordering or identity-sensitive state has different requirements; avoid the blanket claim that an index is always a bug.

Random/changing keys generally force loss of previous identity rather than making a list more correct. A stable database/domain ID is often a useful choice when it represents the actual item identity.

### 8.2 Preserving versus resetting an editor

An unrelated parent update kept Ada's note. Changing the editor key from Ada to Lin reset its local note. Switching back to Ada created a fresh editor; keys did not act as a cache of every unmounted person's state. Persist drafts explicitly at a suitable owner if that is the requirement. [Preserving/resetting state](https://react.dev/learn/preserving-and-resetting-state)

---

## 9. Effects: synchronize external work, then clean it up

An effect is appropriate when committed UI inputs must synchronize with an external system: a subscription, timer, browser integration or a manually managed request. An action caused by a specific click often belongs in its handler. A filtered array or full name calculated from state usually belongs in rendering. [You might not need an effect](https://react.dev/learn/you-might-not-need-an-effect)

```jsx
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
```

The subscription is a local external-resource model: an object enters a Set on setup and leaves on cleanup. It is not a real WebSocket or third-party subscription service. Browser tests measure the actual effect lifecycle and resource count.

### 9.1 Dependencies describe reactive inputs

React compares declared dependencies with Object.is. An object/function freshly created on every render can therefore be different even if it looks similar. Include the reactive values the effect uses, and restructure unnecessary object/function creation where appropriate. Omitting a dependency to silence a warning can leave stale values in the effect.

| Dependency form | Intended relationship |
| --- | --- |
| Omitted array | Synchronize after each relevant committed render |
| Empty array | No changing reactive inputs declared; mount/unmount lifecycle still matters |
| Explicit values | Resynchronize when one changes according to comparison |

Empty dependencies do not mean once forever: remounts and development Strict Mode can create additional lifecycles. Neither adding every unrelated variable nor omitting used values expresses a correct dependency design. [useEffect reference](https://react.dev/reference/react/useEffect)

### 9.2 Cleanup ordering: actual result

```json
[
  {
    "type": "subscription-setup",
    "topic": "react"
  },
  {
    "type": "subscription-cleanup",
    "topic": "react"
  },
  {
    "type": "subscription-setup",
    "topic": "node"
  }
]
```

An unrelated update with the same topic did not reconnect. Changing react to node cleaned the old resource before setting up the new one. Conditional unmount removed the subscription; remount created one new resource. Root unmount removed both the owned DOM and remaining subscription.

Cleanup must undo the setup it belongs to. An unsubscribe function should refer to that subscription, not accidentally close whichever new connection a shared variable now points at. Browser request cancellation and obsolete-result suppression appear in the API example below. [Synchronizing effects](https://react.dev/learn/synchronizing-with-effects)

---

## 10. Strict Mode: development probes, not a production double-call rule

Strict Mode enables development checks that help reveal impure rendering and missing cleanup. In the tested root Strict Mode configuration, the subscription followed setup → cleanup → setup on initial development mounting. Correct cleanup left one active resource. The production build had one setup, even though the root still used StrictMode.

```json
{
  "development": [
    {
      "type": "subscription-setup",
      "topic": "react"
    },
    {
      "type": "subscription-cleanup",
      "topic": "react"
    },
    {
      "type": "subscription-setup",
      "topic": "react"
    }
  ],
  "production": [
    {
      "type": "subscription-setup",
      "topic": "react"
    }
  ]
}
```

Do not memorize every component always renders exactly twice. Which checks run depends on development/production, placement and lifecycle; React's official guide distinguishes a root Strict Mode boundary from a subtree boundary. The fixture explicitly compares **root development and production** bundles. [Strict Mode](https://react.dev/reference/react/StrictMode)

Turning the checks off can hide the symptom without fixing leaked resources. Make setup/cleanup symmetric and keep render/updater logic pure. Do not initiate a payment or other irreversible action merely because a component effect mounted; revisit M9/M15 for durable operation semantics.

---

## 11. Controlled forms and accessible interactions

A controlled text input receives its value from state and updates that state through an event handler. A controlled checkbox uses checked and the event's checked value. An uncontrolled input can keep its current value in the DOM, often with an initial defaultValue and a ref/form API for access. Do not accidentally switch between controlled and uncontrolled ownership during its lifetime. [React input reference](https://react.dev/reference/react-dom/components/input)

```jsx
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
```

The form begins with a defined empty string, prevents default navigation, trims on submit and distinguishes invalid/saved states. Browser tests type into the field, submit with Enter, verify the linked error and confirm that success clears aria-invalid. The saved name is local UI state; it is not a verified database write.

### 11.1 Semantic HTML first

Use a button for actions, a link for navigation, a label for an input, and useful headings/lists/landmarks. Native controls provide keyboard behavior that a clickable div would require you to rebuild. Preserve visible focus, accessible names and understandable feedback. A placeholder alone is a poor substitute for a persistent label. [Semantic HTML and accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML)

The actual checks establish document language/main landmark, an input linked to its validation error, programmatic focus, Space activation of a native button and absence of horizontal overflow at a narrow viewport. These checks and screenshot inspection do **not** establish WCAG conformance or a comprehensive screen-reader audit.

### 11.2 CSS refresher

The box model separates content, padding, border and margin. box-sizing:border-box makes the declared width include padding/border, which simplifies form sizing. Grid/Flexbox handle layout; responsive rules adapt to available space. The fixture uses two columns when room permits and one column below its chosen breakpoint, with a viewport meta tag and visible focus styling. [Box model](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Box_model), [responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)

No fixed breakpoint fits every application. Test the content and interactions at realistic widths instead of treating one mobile screenshot as exhaustive responsive validation. Tailwind's utility syntax follows in M21; it does not remove these CSS/layout requirements.

---

## 12. API state: idle, loading, success, empty and error

An API-driven UI must represent more than items-or-null. Define what is visible before a request, during it, after an empty success, after data arrives and after a failure. Keep the current query/result relationship explicit so old results do not masquerade as the new query.

```text
Idle -> query submitted -> Loading
                         -> Success with items
                         -> Success with empty result
                         -> Error -> retry current query -> Loading
Query changes/unmount -> old work is no longer authoritative
```

fetch normally resolves with a Response for HTTP error statuses; check response.ok/status deliberately. Network errors, invalid JSON and an invalid success schema are separate failure possibilities. AbortController can request cancellation, but you still need a policy for results that complete after their owner becomes obsolete. [Fetch behavior](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch), [AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

### 12.1 The executable data hook

```javascript
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
```

The hook declares query, retry revision, loader and event callback dependencies. Imported loaders/record functions are stable in this fixture. Replacing them with newly created functions on every parent render can change the effect lifecycle; do not silently remove them from dependencies to mask that.

Runtime validation requires a bounded item array, string IDs/titles and unique IDs for the rendered list. It is a small teaching contract, not a complete production API schema. The HTTP server is a controlled local fixture; no real authentication, database or business-side effect is involved.

### 12.2 The actual presentation component

```jsx
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
```

Loading uses a live region/busy state; failure gets a visible message and retry; an empty success is distinct from failure. API titles are ordinary React text children. A literal img-tag string remained text, with no img element created. This is evidence for the tested text boundary, not a full XSS audit; unsafe HTML injection and untrusted URLs require their own design.

The retry button changes a revision so the current query can be requested again after the fixture recovers. Disabling/changing UI controls alone would not make a mutating backend operation idempotent. Here every data request is read-only; use M6/M9/M15 for write/retry correctness.

---

## 13. Race conditions: cancellation and obsolete-result suppression

Suppose the user requests slow, then fast. If slow finishes last and blindly sets state, the screen can display stale results for the new query. The effect's active flag identifies whether its completion still belongs to the current lifecycle. Cleanup sets it false and also aborts the controller.

Two actual browser experiments verify distinct protections:

| Experiment | Mechanism exercised | Observed evidence |
| --- | --- | --- |
| Normal loader: slow then node | Browser fetch receives the AbortSignal | Old request disconnect recorded by the local server; Node.js result displayed |
| Special loader ignores the signal: slow then fast | Active-lifecycle check remains necessary | Old real HTTP response completes, is marked ignored, and Fast result remains visible |

Exact second experiment:

```json
{
  "newer_visible": [
    "Fast result"
  ],
  "events": [
    {
      "type": "request-start",
      "query": "slow"
    },
    {
      "type": "request-cleanup",
      "query": "slow"
    },
    {
      "type": "request-start",
      "query": "fast"
    },
    {
      "type": "request-success",
      "query": "fast"
    },
    {
      "type": "ignored-result",
      "query": "slow"
    }
  ]
}
```

The server holds the slow response until the verifier releases it after the newer result appears. This establishes the ordering without relying on a narrow sleep. The ignore-abort loader is deliberately for this experiment, not the normal recommended transport path.

Unmounting the topic panel also aborts its pending normal request and removes the view. Cancellation does not undo work already committed on a remote backend; here it only concerns a read-only response and client ownership. A real job/payment path needs durable identifiers and reconciliation, not just AbortController.

Framework data loading or a dedicated query/cache library can address caching, deduplication, navigation, preloading and invalidation more comprehensively. This hand-written hook teaches mechanisms and their limitations; it does not replace a production data layer automatically.

---

## 14. Context, memo, useMemo and useCallback

Context passes a value to consumers through a provider boundary without forwarding a prop at every intermediate component. It does not store every application value by itself or eliminate update costs. Consumers observe provider value changes; fresh object values can change identity even when fields look the same. [useContext](https://react.dev/reference/react/useContext)

```jsx
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
```

The consumer observed a theme change. The provider holds a primitive string, keeping the example's ownership clear. Use ordinary props/composition when they communicate the relationship well; avoid turning all local state into one broad context value.

| Tool | Reuses/skips what? | Important boundary |
| --- | --- | --- |
| memo | Can skip a component render for unchanged props | Own state/context changes and other behavior still matter |
| useMemo | Caches a calculated value for dependencies | Calculation must be pure; it is a performance tool |
| useCallback | Caches a function reference for dependencies | Does not execute the function or fix stale captures automatically |

The fixture uses a stable callback and primitive label prop. An unrelated parent update produced no additional child-commit diagnostic in that run. Changing the label produced a new child commit and updated derived text. Clicking the cached callback still requested a parent state update. The commit diagnostic is recorded in an effect, not by mutating data during render.

These are specific observed behaviors with React Compiler disabled, not guarantees about every scheduling situation or a benchmark of optimization value. Profile before adding caches throughout an application. [memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback)

---

## 15. Architectural understanding: build an API-driven React screen

### 15.1 Requirements and component/data map

Assume a placement topic explorer: a user enters a query, sees loading/error/empty/results and can keep a local draft note for an item. Ask whether queries should run on submit or typing, whether drafts survive navigation, what permission scope the API enforces, and what should happen when requests overlap.

```text
TopicScreen
  owns draft query / submitted query / selected item
  |
  +-- SearchForm: controlled value + submit callback
  +-- useTopics/data layer: request lifecycle + validated result
  +-- Status: idle/loading/error/empty feedback
  +-- TopicList: stable item keys
       +-- TopicRow: item props + deliberate draft owner

HTTP API
  validates input and authenticates/authorizes tenant/user
  accesses data and returns a stable response contract
```

The fixture demonstrates these UI mechanisms in separate small panels. A real screen would choose a coherent product flow instead of exposing test controls. The release/recover buttons are local harness controls, not production API features.

### 15.2 Implementation order

1. **Build semantic static markup.** Identify components, headings, forms, list identity and accessible control names.
2. **Choose state owners.** Keep query/draft/selection where their sharing and persistence requirements demand; derive counts/filtered data.
3. **Implement event behavior.** Keep controlled input updates fast and make submit semantics explicit. Validate for useful feedback while retaining backend validation.
4. **Add the data boundary.** Represent all request states, check HTTP/schema, and keep current query/results aligned.
5. **Handle lifecycle and races.** Abort obsolete read requests, ignore inactive results and test unmount/reorder interactions.
6. **Add sharing deliberately.** Use callbacks/context when appropriate; avoid broad state and fresh value identities without a reason.
7. **Verify actual user behavior.** Exercise keyboard input, errors/retry, stale response ordering, identity and narrow layouts.
8. **Measure before optimizing.** Locate costly work with relevant profiling, then evaluate memoization or data-layer changes under the same conditions.

### 15.3 Diagnose three common bugs

**An edited draft moves to another row:** inspect stable data identity and keys before blaming the input handler. State may have followed the component's positional identity.

**A subscription reconnects on every keystroke:** inspect dependencies and freshly created objects/functions, then distinguish legitimate resynchronization from avoidable identity changes. Do not remove a used dependency without redesigning the effect.

**Search shows the previous query's result:** inspect completion order, the state/query relationship, cleanup and cancellation. A successful old request can still be obsolete. Use a controlled race test instead of assuming network requests finish in submission order.

### 15.4 Resume explanation

In 30 seconds, explain React as components describing UI from props/state, with updates leading to render/commit. In two minutes, add state ownership, identity and effect lifecycle. In five minutes, trace form → request → validation → status/results, including a late response, cleanup and backend authorization boundary.

For your resume's dashboards/full-stack work, describe the exact component/data path and what you implemented. The fixture does not establish your project's actual architecture, performance gains, accessibility compliance or production framework version.

---

## 16. Must remember and common wrong answers

| Say this | Avoid this |
| --- | --- |
| React calculates UI from current inputs | React is the JavaScript language or the backend database |
| A setter requests a new snapshot | It rewrites the current handler's state variable |
| Pure functional updaters compose previous-state changes | Three replacements necessarily mean three increments |
| Copy changed nested paths | Object spread always deeply clones state |
| Type/position/key establish identity | An index always represents the same logical item |
| Effects synchronize external work with cleanup | Every calculated value belongs in an effect |
| Dependencies include used reactive inputs | Delete dependencies until reconnecting stops |
| Root development Strict Mode probes cleanup | Every production component always runs exactly twice |
| Refs persist mutable handles without requesting render | Ref mutation automatically updates displayed state |
| Check HTTP status/schema and current request ownership | fetch rejects every HTTP 500 or finishes in request order |
| Context shares a value; caches optimize chosen work | Context/memo automatically make every screen faster |
| Browser UI validation complements backend checks | Hidden buttons and client checks enforce permissions |

---

## 17. Interview questions and follow-ups

### Q1. What is React, and why use it?

A UI library for composing components and keeping rendered output consistent with their inputs/state. It provides a declarative way to manage changing screens. It still requires browser/HTML/CSS knowledge, a data boundary and suitable application architecture.

### Q2. React versus JavaScript, React DOM and Next.js?

JavaScript is the language; React describes component UI; React DOM renders it into the web DOM. Next.js adds framework behavior such as routing and server/client rendering conventions. The standalone browser fixture does not exercise those framework features.

### Q3. What is JSX?

Syntax transformed into JavaScript element descriptions. It supports JavaScript expressions and React conventions; it is not an arbitrary HTML string. JSX compilation and React Compiler performance optimization are distinct. Ordinary string children are rendered as text, as the API string test demonstrates.

### Q4. Props versus state?

Props are inputs from an owner; state is changing memory associated with a component identity. Treat both as render snapshots and existing data as immutable. A parent can pass its state as a child's prop and a callback for requesting changes.

### Q5. What happens after a state update?

React schedules/calculates a new UI description and commits necessary changes; the browser can then lay out/paint. A render function call is not the same as replacing every DOM node. The currently running handler still has the values it captured.

### Q6. Why did three setCount(count + 1) calls add one?

They used the same count snapshot and requested the same replacement value. Three pure functional updaters instead compose through queued previous values. The browser fixture observed one versus three increments from zero.

### Q7. Why does a stored callback see an old count?

It closed over the values from its render. Decide whether the operation should use the captured value, a functional previous-state update or a current ref value. Correct effect dependencies are another part of maintaining intended external callbacks.

### Q8. Why avoid mutating objects/arrays in state?

Mutation changes existing shared data instead of creating a new intended snapshot and can interfere with identity-based comparisons. Copy the affected paths; spread is shallow. The fixture changed both outer/nested references and preserved the previous theme.

### Q9. When should you lift state up?

When multiple components need one coordinated source of truth, move ownership to a useful common parent and pass values/callbacks down. Avoid duplicating a derived count/list in state. Ownership should reflect sharing and persistence requirements, not put everything at the root by default.

### Q10. What are the Rules of Hooks?

The state/effect/ref/context hooks used here are called consistently at the top level of components/custom hooks, not conditionally or in handlers. Extract components or put conditions inside effects where appropriate. The newer use API has distinct documented rules; do not generalize its exceptions to useState.

### Q11. useRef versus useState?

Ref current persists without requesting a render; state controls rendered snapshots through updates. Use refs for deliberate imperative handles/non-rendered mutable data, such as focusing an input. Reading a ref in an event and publishing state is different from expecting ref mutation to repaint the UI.

### Q12. Why do list keys matter?

They describe logical identity among siblings when items move. Wrong identity can attach local state to the wrong data. In the index-key counterexample, Alpha's edited draft appeared under Beta after reordering. Stable IDs preserved the correct draft and input node.

### Q13. Do keys have to be globally unique, and does changing a key cache state?

Keys need uniqueness among the relevant siblings. Changing a key normally creates a new identity and can reset local state. Returning to an old unmounted key does not automatically restore a cached draft; store that draft at an appropriate owner if required.

### Q14. What is useEffect for?

Synchronizing committed inputs with an external system, with cleanup for obsolete work. It is not the default place for derived rendering calculations or a button-specific action. Explain the external resource and lifecycle before adding an effect.

### Q15. What do dependency arrays mean?

They declare reactive inputs whose changes can require resynchronization, compared with Object.is. New object/function identities can change them. Omitting a used value can make the effect stale; an empty array does not mean once across every remount/development lifecycle.

### Q16. When does cleanup run?

Before a replacement setup for changed dependencies and when the component unmounts, with additional development checks possible. The fixture observed old-topic cleanup before new-topic setup and zero resources after unmount. Cleanup should undo the particular setup it belongs to.

### Q17. Why does Strict Mode run an extra effect cycle?

It helps expose missing cleanup in development. The tested root development bundle ran setup/cleanup/setup and retained one subscription; production ran one setup. Placement/lifecycle/version matter, so avoid the unconditional slogan that production renders every component twice.

### Q18. Controlled versus uncontrolled inputs?

A controlled input receives current value/checked from React state and updates through handlers; uncontrolled ownership leaves the current value primarily in the DOM. Choose ownership deliberately and avoid switching it accidentally. Form feedback and backend validation remain separate requirements.

### Q19. Why not store filtered items and their count in separate state?

If they can be calculated from existing data/filter inputs, duplicate state creates synchronization work and stale combinations. Derive them during render, adding caching only for a measured need. The fixture's filtered list and count come from the same calculation.

### Q20. Which states should an API screen show?

Idle, loading, successful data, successful empty result and failure/retry, with a deliberate query/result relationship. Validate HTTP and payload shape. A network request completing does not mean its result still belongs to the current screen or that the server operation was authorized correctly.

### Q21. Does fetch reject an HTTP 503?

Not merely because of that status: check response.ok/status explicitly. Network failures and parse/schema failures are additional cases. The browser fixture converts a real local 503 and a malformed successful payload into visible failure states.

### Q22. How do you prevent stale search responses?

Cancel obsolete work where supported and suppress completions that no longer belong to the active lifecycle/query. The controlled race test let an old real response complete despite ignored cancellation; the active check kept the newer Fast result visible.

### Q23. Does AbortController undo a backend write?

No. It can stop client work/waiting and signal supported operations, but a remote effect may already have committed. Durable operation IDs, idempotency and reconciliation handle write ambiguity. This fixture only tests read-response ownership.

### Q24. Does a custom hook share one global state instance?

No: it shares reusable logic, and separate calls can have independent state. Choose a common owner, provider or appropriate external/query store when shared data is required. A hook's name alone does not define a singleton cache.

### Q25. What is context, and when is it useful?

A provider supplies a value to consumers without passing it through every intermediate prop. It is useful for deliberate shared concerns such as a theme. Value identity/update scope still matter; context is not automatic persistence, authorization or a free performance improvement.

### Q26. memo versus useMemo versus useCallback?

memo can skip component rendering for unchanged props; useMemo caches a calculated value; useCallback caches a function reference. Dependencies/captured values remain important. They are performance tools, not substitutes for correct state ownership or guarantees that work never repeats.

### Q27. Why can a memoized child still update?

Its own state/context may change, props may have new identities, and memo is an optimization rather than a semantic requirement. The fixture observed a skip for stable props and an update after a changed label, with React Compiler disabled; it did not benchmark a universal speedup.

### Q28. What accessibility basics belong in a React form?

Semantic controls, persistent labels, keyboard operation, visible focus and understandable linked errors/status feedback. Preserve native form behavior where appropriate. The fixture tests selected browser interactions and layout, not full screen-reader/WCAG conformance.

### Q29. How would you debug a UI state bug?

Identify the intended owner, current props/state snapshot, component identity and event/effect that requests a change. For row mix-ups inspect keys; for reconnects inspect dependencies; for stale data inspect completion ordering and cleanup. Avoid adding caches/effects before locating the boundary.

### Q30. Design an API-driven React topic explorer in five minutes.

Draw controlled search → owned query/data lifecycle → status/results → stable keyed rows, then define draft persistence, runtime validation, cancellation and stale-result policy. Add keyboard/feedback/layout checks and backend authorization. Explain which behavior is verified and reserve framework SSR/routing/cache details for M21.

---

## 18. Practice tasks

1. **Trace a state event.** Compare three replacements/updaters and explain handler snapshot versus later DOM output.
2. **Inspect a closure/ref.** Capture a callback, change state, invoke it and distinguish captured state from a mutable ref read.
3. **Update nested state.** Show which references change and why a shallow copy alone may leave shared nested data.
4. **Reorder editable rows.** Compare stable IDs with the index counterexample and inspect logical draft/DOM identity.
5. **Choose a draft owner.** Preserve a draft across an unrelated update, reset by key, then design explicit persistence across unmount.
6. **Audit an effect.** Explain dependencies, setup/cleanup order, remount and the root development/production comparison.
7. **Build an accessible form.** Test Enter/Space/focus, controlled text/checkbox state and linked error/status feedback.
8. **Break the API boundary.** Reproduce loading, empty, 503/recovery, malformed success and literal markup text.
9. **Force a race.** Release a held old response after a newer result, both with normal abort and the ignore-abort fixture; explain the two protections.
10. **Design and diagnose.** Draw the explorer's state/component/API map, select sharing/memoization deliberately and name the evidence needed before a performance claim.

---

## 19. Exit checklist

- [ ] I can distinguish React, React DOM, JavaScript, JSX and a framework.
- [ ] I can explain props/state, pure render, commit and browser paint.
- [ ] I can predict snapshot/updater/closure behavior without calling setters synchronous assignments.
- [ ] I can update nested data immutably and derive redundant values.
- [ ] I can choose state ownership and distinguish refs from rendered state.
- [ ] I can explain stable keys, preservation, reset and unmounted drafts.
- [ ] I can justify an effect's external resource, dependencies and cleanup.
- [ ] I can explain the tested Strict Mode development/production difference.
- [ ] I can build controlled semantic forms with useful keyboard/error feedback.
- [ ] I can represent API states, validate responses and suppress obsolete results.
- [ ] I can distinguish context/memo/useMemo/useCallback and their limits.
- [ ] I can describe a complete React/API architecture without inventing framework/backend verification.

These learning checks remain unchecked until you can demonstrate them.

---

## 20. Sources and verification map

Primary references researched:

- React foundations: [JSX](https://react.dev/learn/writing-markup-with-jsx), [props](https://react.dev/learn/passing-props-to-a-component), [purity](https://react.dev/learn/keeping-components-pure), [render/commit](https://react.dev/learn/render-and-commit), [snapshots](https://react.dev/learn/state-as-a-snapshot), [update queues](https://react.dev/learn/queueing-a-series-of-state-updates), [object updates](https://react.dev/learn/updating-objects-in-state), [state sharing](https://react.dev/learn/sharing-state-between-components) and [Thinking in React](https://react.dev/learn/thinking-in-react).
- React lifecycle/identity: [lists/keys](https://react.dev/learn/rendering-lists), [state identity](https://react.dev/learn/preserving-and-resetting-state), [effect synchronization](https://react.dev/learn/synchronizing-with-effects), [unnecessary effects](https://react.dev/learn/you-might-not-need-an-effect), [useEffect](https://react.dev/reference/react/useEffect), [Strict Mode](https://react.dev/reference/react/StrictMode), [hook rules](https://react.dev/reference/rules/rules-of-hooks) and [refs](https://react.dev/reference/react/useRef).
- React sharing/forms: [inputs](https://react.dev/reference/react-dom/components/input), [context](https://react.dev/reference/react/useContext), [memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback) and the separate [use API](https://react.dev/reference/react/use).
- Browser/testing: [Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch), [AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController), [semantic accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML), [box model](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Box_model), [responsive layout](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design) and [Playwright assertions](https://playwright.dev/docs/test-assertions).

Version-sensitive behavior is tied to the recorded bundles/browser. The website's own React/Next tree is separate; older interview examples and newer APIs can use different conventions.

**50 browser checks passed:**

| Group | Named checks | Actual evidence |
| --- | --- | --- |
| State | 8 | Snapshot/replacements/updaters, closure, refs and nested immutable update |
| Identity | 6 | Stable-key draft/node reuse, index counterexample and editor preservation/reset |
| Effects | 6 | Setup/dependency/cleanup/remount and root unmount |
| Strict Mode | 3 | Root development probe, one active resource and production comparison |
| Forms | 6 | Controlled input, validation/Enter, checkbox and derived list/count |
| Sharing | 4 | Context consumer, memo commit behavior, changed props and stable callback |
| API | 11 | Real HTTP states/schema/escaping, retry, browser abort, unmount and completed obsolete response |
| Accessibility/layout | 5 | Selected semantic/error/focus/keyboard/narrow-width assertions |
| Browser health | 1 | No captured uncaught application/React exceptions |
| **Total** | **50** | Named actual browser checks, not a complete accessibility/performance audit |

Files are under examples/resume-skills/module-20-react/. main.jsx assembles the independent practice panels; diagnostics.js records test-only event/effect observations. The chapter embeds StateLab.jsx, IdentityLab.jsx, EffectsLab.jsx, FormsLab.jsx, ContextLab.jsx, TopicsPanel.jsx and useTopics.js exactly. server.mjs owns static assets, local API and test response controls; build.mjs emits development/production bundles, serve.mjs is the optional manual entrypoint and verify.mjs runs the headless checks.

verification-results.json and verification-output.txt record checks/versions/observations; cleanup-results.json records browser/listener closure. browser-desktop.png and browser-mobile.png are actual captured layouts inspected during authoring. browser-build-output.txt, dependency-audit.json and content/site validation artifacts are stored alongside them. Generated bundles and node_modules are ignored and reproducible from the recorded sources/lockfile.

No framework SSR/hydration, React Compiler, real authenticated backend/storage, cross-browser suite, assistive-technology audit, production security/compliance or performance benchmark was executed. The old-response and index-key cases are deliberate teaching counterexamples. All authoring listeners/browser resources were closed, and Docker was not started.

---

## Next

Continue to [M21: Next.js, API Routes and Tailwind](/docs/resume-skills/nextjs-api-routes-tailwind) for framework routing/layouts, server/client rendering, hydration, data/cache boundaries, API handlers and utility-based styling. The resume's Next.js 14 context and the study website's installed version will be distinguished explicitly.

Revisit [M6: REST APIs](/docs/resume-skills/rest-apis-http) for response contracts, [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) for trusted authorization, and [M19: Testing/Observability](/docs/resume-skills/git-ci-cd-testing-observability-performance) for evidence and performance claims. The [master roadmap](/docs/resume-skills) shows the remaining sections.
