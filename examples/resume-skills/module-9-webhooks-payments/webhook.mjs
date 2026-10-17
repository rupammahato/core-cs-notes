import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
export class IntegrationError extends Error {
  constructor(status, code) { super(code); Object.assign(this, { status, code }); }
}
export const fail = (status, code) => { throw new IntegrationError(status, code); };
export const sign = (raw, secret) => createHmac('sha256', secret).update(raw).digest('hex');
export function verifySignature(raw, signature, secrets) {
  if (typeof signature !== 'string' || !/^[a-fA-F0-9]{64}$/.test(signature)) fail(401, 'invalid_signature');
  const received = Buffer.from(signature, 'hex');
  const matches = secrets.map(secret => timingSafeEqual(Buffer.from(sign(raw, secret), 'hex'), received));
  if (!matches.some(Boolean)) fail(401, 'invalid_signature');
}
const id = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,80}$/.test(value);
export function parseEvent(raw, endpoint) {
  let value;
  try { value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw)); }
  catch { fail(400, 'invalid_json'); }
  if (!value || value.entity !== 'event' || typeof value.event !== 'string' || value.event.length > 80)
    fail(400, 'invalid_event');
  if (value.account_id !== endpoint.accountId) fail(403, 'account_mismatch');
  const expected = new Map([
    ['payment.authorized', 'authorized'], ['payment.captured', 'captured'], ['payment.failed', 'failed'],
  ]).get(value.event);
  if (!expected) return { type: value.event, ignored: true };
  const payment = value.payload?.payment?.entity;
  if (!payment || payment.entity !== 'payment' || !id(payment.id) || !id(payment.order_id) ||
      !Number.isSafeInteger(payment.amount) || payment.amount <= 0 ||
      typeof payment.currency !== 'string' || !/^[A-Z]{3}$/.test(payment.currency) ||
      payment.status !== expected) fail(400, 'invalid_payment');
  return {
    type: value.event, paymentId: payment.id, providerOrderId: payment.order_id,
    amount: payment.amount, currency: payment.currency, status: expected,
  };
}
export function receive({ endpointId, endpoints, store, raw, signature, eventId }) {
  const endpoint = Object.hasOwn(endpoints, endpointId) ? endpoints[endpointId] : undefined;
  if (!endpoint) fail(404, 'not_found');
  if (!id(eventId)) fail(400, 'invalid_event_id');
  verifySignature(raw, signature, endpoint.secrets);
  const event = parseEvent(raw, endpoint);
  const rawHash = createHash('sha256').update(raw).digest('hex');
  return store.accept(endpointId, eventId, rawHash, event);
}
