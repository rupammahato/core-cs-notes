import { revalidateTag } from 'next/cache';

// Test-harness control only; a production invalidation endpoint needs real authorization.
export async function POST(request: Request) {
  if (request.headers.get('x-fixture-key') !== process.env.M21_CONTROL_KEY) {
    return Response.json({ error: 'Forbidden' }, { status: 403 });
  }
  revalidateTag('m21-public');
  return Response.json({ invalidated: 'm21-public' });
}
