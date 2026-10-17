import type { NextApiRequest, NextApiResponse } from 'next';
import { parseMessage } from '../../lib/contract';

export default function handler(request: NextApiRequest, response: NextApiResponse) {
  response.setHeader('Cache-Control', 'no-store');
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ error: 'Method not allowed' });
  }
  if (request.headers['content-type']?.split(';')[0].trim() !== 'application/json') {
    return response.status(415).json({ error: 'JSON required' });
  }
  const message = parseMessage(request.body);
  if (message === null) return response.status(422).json({ error: 'Invalid message' });
  return response.status(200).json({ message, persisted: false });
}
export const config = { api: { bodyParser: { sizeLimit: '1kb' } } };
