import Link from 'next/link';
import Counter from '../../components/Counter';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <section className="card space-y-6"><h1 className="text-3xl font-bold">Practice dashboard</h1>
    <Counter label="layout counter" />
    <nav aria-label="Dashboard" className="flex gap-4 underline">
      <Link href="/dashboard" prefetch={false}>Overview</Link>
      <Link href="/dashboard/settings" prefetch={false}>Settings</Link>
    </nav><div>{children}</div>
  </section>;
}
