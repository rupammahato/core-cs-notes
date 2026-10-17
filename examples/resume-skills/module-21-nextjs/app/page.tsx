import Link from 'next/link';
import Counter from '../components/Counter';
import TopicLookup from '../components/TopicLookup';
import { listTopics, serverConfigured } from '../lib/topics';

export default function Home() {
  const topics = listTopics();
  return <div className="space-y-6">
    <h1 className="text-3xl font-bold">Placement topic explorer</h1>
    <p>Server data, a hydrated client island and a browser API request.</p>
    <p data-testid="configured">Server configured: {String(serverConfigured())}</p>
    <div data-testid="cards" className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <section className="card space-y-4"><h2 className="text-xl font-semibold">Server-rendered topics</h2>
        <ul className="list-inside list-disc">{topics.map(topic => <li key={topic.slug}>
          <Link className="underline" prefetch={false} href={`/catalog/${topic.slug}`}>{topic.title}</Link>
        </li>)}</ul><Counter label="home counter" />
      </section>
      <section className="card space-y-4"><h2 className="text-xl font-semibold">Client API lookup</h2><TopicLookup /></section>
    </div>
  </div>;
}
