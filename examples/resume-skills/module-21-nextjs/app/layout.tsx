import Link from 'next/link';
import './globals.css';

export const metadata = { title: 'M21 Next.js 14 practice', description: 'Isolated placement teaching fixture' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className="bg-slate-100 text-slate-900">
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
      <header className="space-y-3"><p className="font-semibold">M21 · Next.js 14 / Tailwind 3</p>
        <nav aria-label="Main" className="flex flex-wrap gap-4 underline">
          <Link href="/" prefetch={false}>Home</Link>
          <Link href="/catalog/node" prefetch={false}>Node topic</Link>
          <Link href="/dashboard" prefetch={false}>Dashboard</Link>
          <Link href="/cache" prefetch={false}>Cache lab</Link>
        </nav>
      </header><main>{children}</main>
      <footer className="text-sm text-slate-600">Local teaching data. No login, database or external service.</footer>
    </div>
  </body></html>;
}
