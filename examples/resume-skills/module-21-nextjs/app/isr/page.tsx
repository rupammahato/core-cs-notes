export const revalidate = 1;
export default async function IsrPage() {
  const response = await fetch(`${process.env.M21_ORIGIN}/isr`, { next: { revalidate: 1 } });
  if (!response.ok) throw new Error('Origin unavailable');
  const data = await response.json();
  if (typeof data.version !== 'number') throw new Error('Invalid version');
  return <section className="card"><h1 className="text-3xl font-bold">ISR lab</h1>
    <output data-testid="isr-version">{data.version}</output>
  </section>;
}
