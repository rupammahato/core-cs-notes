import { randomUUID } from 'node:crypto';
import { notFound } from 'next/navigation';
import { findTopic, listTopics } from '../../../lib/topics';

export const dynamicParams = false;
export function generateStaticParams() { return listTopics().map(({ slug }) => ({ slug })); }
export default function TopicPage({ params }: { params: { slug: string } }) {
  const topic = findTopic(params.slug);
  if (!topic) notFound();
  return <article className="card space-y-4"><h1 className="text-3xl font-bold">{topic.title}</h1>
    <p>{topic.summary}</p><p>Public topic; prebuilt for the recorded build.</p>
    <p data-testid="static-stamp">{randomUUID()}</p>
  </article>;
}
