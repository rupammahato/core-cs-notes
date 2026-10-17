import { parseMessage } from '../../../lib/contract';

export const runtime = 'nodejs';
export async function POST(request: Request) {
  const headers = { 'Cache-Control': 'no-store' };
  if (request.headers.get('content-type')?.split(';')[0].trim() !== 'application/json') {
    return Response.json({ error: 'JSON required' }, { status: 415, headers });
  }
  let value: unknown;
  try { value = await request.json(); }
  catch { return Response.json({ error: 'Malformed JSON' }, { status: 400, headers }); }
  const message = parseMessage(value);
  if (message === null) return Response.json({ error: 'Invalid message' }, { status: 422, headers });
  return Response.json({ message, persisted: false }, { headers });
}
