'use client';
import { useEffect, useState } from 'react';

export default function Counter({ label }: { label: string }) {
  const [count, setCount] = useState(0);
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => { setHydrated(true); }, []);
  return <section aria-label={label} className="space-y-3">
    <p>{label}: <output>{count}</output></p>
    <button className="action" onClick={() => setCount(value => value + 1)}>Increment {label}</button>
    <p data-testid={`${label}-hydrated`}>{hydrated ? 'Hydrated' : 'HTML preview'}</p>
  </section>;
}
