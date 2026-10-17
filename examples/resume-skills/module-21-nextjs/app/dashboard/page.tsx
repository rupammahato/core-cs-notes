import { cookies } from 'next/headers';
import { randomUUID } from 'node:crypto';

export default function Dashboard() {
  const label = cookies().get('demo_label')?.value.slice(0, 40) || 'Visitor';
  return <section className="space-y-3"><h2 className="text-xl font-semibold">Overview</h2>
    <p data-testid="visitor">Display label: {label}</p><p>This cookie is untrusted display data, not authentication.</p>
    <p data-testid="dynamic-stamp">{randomUUID()}</p>
  </section>;
}
