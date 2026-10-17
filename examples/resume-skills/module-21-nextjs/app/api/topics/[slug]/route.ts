import { findTopic } from '../../../../lib/topics';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function GET(_request: Request, { params }: { params: { slug: string } }) {
  const topic = findTopic(params.slug);
  return Response.json(topic || { error: 'Topic not found' }, {
    status: topic ? 200 : 404, headers: { 'Cache-Control': 'no-store' },
  });
}
