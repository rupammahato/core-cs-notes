export const dynamic = 'force-dynamic';
export default async function BrokenPage() {
  const response = await fetch(`${process.env.M21_ORIGIN}/unstable`, { cache: 'no-store' });
  if (!response.ok) throw new Error('M21_PRIVATE_FAILURE_DETAILS');
  return <section className="card"><h1 className="text-3xl font-bold">Recovered server content</h1></section>;
}
