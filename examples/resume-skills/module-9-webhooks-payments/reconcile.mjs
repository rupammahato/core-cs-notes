import { createHash } from 'node:crypto';
import { parseEvent, fail } from './webhook.mjs';

// Trusted worker API, not an unauthenticated HTTP route.
// fetchPayment is an account-bound provider client; the tests supply a local fixture.
export async function reconcilePayment({ endpointId, endpoints, store, paymentId, fetchPayment }) {
  const endpoint = Object.hasOwn(endpoints, endpointId) ? endpoints[endpointId] : undefined;
  if (!endpoint) fail(404, 'not_found');
  const snapshot = await fetchPayment({ endpointId, paymentId });
  if (snapshot.accountId !== endpoint.accountId) fail(502, 'provider_account_mismatch');
  if (snapshot.payment?.id !== paymentId) fail(502, 'provider_payment_mismatch');
  if (!['authorized', 'captured', 'failed'].includes(snapshot.payment.status))
    return { outcome: 'unresolved' };
  const raw = Buffer.from(JSON.stringify({
    entity: 'event', account_id: snapshot.accountId,
    event: 'payment.' + snapshot.payment.status,
    payload: { payment: { entity: snapshot.payment } },
  }));
  const normalized = parseEvent(raw, endpoint);
  const hash = createHash('sha256').update(raw).digest('hex');
  // ':' is forbidden in external delivery IDs, separating internal observations.
  const eventId = 'reconcile:' + hash;
  store.accept(endpointId, eventId, hash, normalized);
  return store.processOne(endpointId, eventId);
}
