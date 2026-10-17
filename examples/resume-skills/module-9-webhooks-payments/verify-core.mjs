import { createHash } from 'node:crypto';
import { sign, verifySignature, receive } from './webhook.mjs';
import { openStore } from './store.mjs';
import { endpoints, orders, fixtureEvent } from './fixtures.mjs';
import { assert, check, rejected, save } from './checks.mjs';

let sqlite;
function using(fn, options = {}) {
  const store = openStore(':memory:', options); sqlite = store.sqlite(); store.seed(orders);
  return Promise.resolve().then(() => fn(store)).finally(() => store.close());
}
function ingest(store, eventId, options = {}, endpointId = options.endpoint ?? 'alpha') {
  const raw = Buffer.from(JSON.stringify(fixtureEvent(options)));
  return receive({ endpointId, endpoints, store, raw, signature: sign(raw, endpoints[endpointId].secrets[0]), eventId });
}
const balance = (store, tenant = 'alpha') => store.snapshot().balances.find(row => row.tenant === tenant)?.credits ?? 0;
await check('HMAC SHA256 matches RFC 4231 known vector', async () => {
  const digest = sign(Buffer.from('Hi There'), Buffer.alloc(20, 0x0b));
  assert.equal(digest, 'b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7');
  return digest;
});
await check('verification preserves raw whitespace and rejects reserialization', async () => {
  const raw = Buffer.from('{ "a": 1, "b": 2 }'), signature = sign(raw, 'secret');
  verifySignature(raw, signature, ['secret']);
  await rejected(async () => verifySignature(Buffer.from(JSON.stringify(JSON.parse(raw))), signature, ['secret']), 401, 'invalid_signature');
  return { exactBytesAccepted: true, reserializedRejected: true };
});
await check('old secret works only while explicitly configured', async () => {
  const raw = Buffer.from('body'), signature = sign(raw, 'old');
  verifySignature(raw, signature, ['new', 'old']);
  return rejected(async () => verifySignature(raw, signature, ['new']), 401, 'invalid_signature');
});
await using(async store => {
  await check('acceptance is inbox commit rather than credit completion', async () => {
    assert.throws(() => openStore(), /Supply a database path/);
    assert.deepEqual(store.configuration(), { journal: 'memory', synchronous: 2, foreignKeys: 1 });
    const receipt = ingest(store, 'event-1');
    assert.equal(receipt.state, 'pending'); assert.equal(balance(store), 0);
    assert.equal(store.snapshot().inbox.length, 1);
    return { state: receipt.state, credits: 0, inboxRows: 1 };
  });
  await check('worker commits credit, paid order, receipt and outbox together', async () => {
    assert.equal(store.processNext().reason, 'granted');
    const state = store.snapshot();
    assert.equal(balance(store), 100); assert.equal(state.ledger.length, 1);
    assert.equal(state.orders.find(row => row.local_id === 'a-1').state, 'paid');
    assert.equal(state.inbox[0].state, 'processed'); assert.equal(state.outbox.length, 1);
    return { credits: 100, ledgerRows: 1, order: 'paid', receipt: 'processed', outboxRows: 1 };
  });
  await check('same event replay returns duplicate without a second effect', async () => {
    assert.equal(ingest(store, 'event-1').duplicate, true);
    assert.equal(store.processOne('alpha', 'event-1').outcome, 'processed');
    assert.equal(balance(store), 100); assert.equal(store.snapshot().outbox.length, 1);
    return { duplicate: true, credits: 100, outboxRows: 1 };
  });
  await check('new delivery ID for same signed payment cannot grant twice', async () => {
    ingest(store, 'event-2');
    assert.equal(store.processNext().reason, 'already_granted');
    assert.equal(balance(store), 100); assert.equal(store.snapshot().ledger.length, 1);
    return { receiptRows: 2, ledgerRows: 1, credits: 100 };
  });
  await check('captured then authorized or failed cannot downgrade capture/order', async () => {
    ingest(store, 'event-auth', { type: 'payment.authorized' }); store.processNext();
    ingest(store, 'event-fail', { type: 'payment.failed' }); store.processNext();
    assert.equal(store.snapshot().payments[0].state, 'captured');
    assert.equal(store.snapshot().orders.find(row => row.local_id === 'a-1').state, 'paid');
    assert.equal(balance(store), 100);
    return { payment: 'captured', order: 'paid', credits: 100 };
  });
  await check('second captured payment for funded order enters review', async () => {
    ingest(store, 'event-second-payment', { paymentId: 'pay_alpha_2' });
    assert.equal(store.processNext().reason, 'order_already_funded');
    assert.equal(balance(store), 100);
    return { reason: 'order_already_funded', credits: 100 };
  });
});
await using(async store => {
  await check('failed attempt does not close order to a later successful attempt', async () => {
    ingest(store, 'failed-attempt', { type: 'payment.failed', paymentId: 'pay_failed' }); store.processNext();
    assert.equal(balance(store), 0);
    assert.equal(store.snapshot().orders.find(row => row.local_id === 'a-1').state, 'pending');
    ingest(store, 'successful-attempt', { paymentId: 'pay_success' }); store.processNext();
    assert.equal(balance(store), 100);
    return { failedAttemptCredits: 0, finalOrder: 'paid', credits: 100 };
  });
});
for (const [name, options, reason] of [
  ['wrong amount', { amount: 1 }, 'amount_or_currency_mismatch'],
  ['wrong currency', { currency: 'USD' }, 'amount_or_currency_mismatch'],
  ['unknown order', { providerOrderId: 'order_unknown' }, 'unknown_order'],
  ['other tenant order through alpha endpoint', { providerOrderId: 'order_beta_1' }, 'unknown_order'],
]) await using(async store => {
  await check(name + ' quarantined without credit', async () => {
    ingest(store, 'review-event', options);
    const result = store.processNext(); assert.equal(result.outcome, 'review'); assert.equal(result.reason, reason);
    assert.equal(balance(store), 0); assert.equal(store.snapshot().outbox.length, 0);
    return { state: 'review', reason, credits: 0 };
  });
});
await using(async store => {
  await check('payload notes cannot choose tenant or number of credits', async () => {
    ingest(store, 'untrusted-notes', { extra: { tenantId: 'beta', credits: 999999, notes: { credits: 999999 } } });
    store.processNext(); assert.equal(balance(store, 'alpha'), 100); assert.equal(balance(store, 'beta'), 0);
    return { alphaCredits: 100, betaCredits: 0 };
  });
  await check('payment identity cannot be rebound to a different order', async () => {
    ingest(store, 'identity-conflict', { providerOrderId: 'order_alpha_2', amount: 50000 });
    assert.equal(store.processNext().reason, 'payment_identity_conflict');
    assert.equal(balance(store), 100);
    return { reason: 'payment_identity_conflict', credits: 100 };
  });
});
await using(async store => {
  await check('same provider event ID is scoped to configured endpoint', async () => {
    ingest(store, 'shared-id'); ingest(store, 'shared-id', { endpoint: 'beta', paymentId: 'pay_beta_1' });
    store.processNext(); store.processNext();
    assert.equal(balance(store, 'alpha'), 100); assert.equal(balance(store, 'beta'), 100);
    return { alphaCredits: 100, betaCredits: 100 };
  });
  await check('same endpoint event ID with changed bytes conflicts', async () =>
    rejected(async () => ingest(store, 'shared-id', { paymentId: 'pay_changed' }), 409, 'event_id_conflict'));
});
let failOnce = true;
await using(async store => {
  ingest(store, 'rollback');
  await check('injected failure after ledger insert rolls back every business effect', async () => {
    assert.throws(() => store.processNext(), /injected failure/);
    const state = store.snapshot();
    assert.equal(balance(store), 0); assert.equal(state.ledger.length, 0);
    assert.equal(state.payments.length, 0); assert.equal(state.outbox.length, 0);
    assert.equal(state.inbox[0].state, 'pending');
    assert.equal(state.orders[0].state, 'pending');
    return { credits: 0, ledgerRows: 0, outboxRows: 0, receipt: 'pending' };
  });
  await check('retry after rollback grants once', async () => {
    store.processNext(); assert.equal(balance(store), 100);
    return { credits: 100, ledgerRows: store.snapshot().ledger.length };
  });
}, { onPhase: phase => {
  if (phase === 'after-ledger-write' && failOnce) { failOnce = false; throw new Error('injected failure'); }
} });
await using(async store => {
  ingest(store, 'notify'); store.processNext();
  const effects = new Map();
  let attempts = 0;
  const send = async message => { attempts++; if (!effects.has(message.id)) effects.set(message.id, message.payload); };
  await check('outbox retry after accepted send can repeat delivery but not idempotent sink effect', async () => {
    await assert.rejects(() => store.dispatchOne(send, { afterSend: () => { throw new Error('lost local completion'); } }));
    assert.equal(store.snapshot().outbox[0].state, 'pending');
    await store.dispatchOne(send);
    assert.equal(attempts, 2); assert.equal(effects.size, 1);
    assert.equal(store.snapshot().outbox[0].state, 'sent');
    return { deliveryAttempts: attempts, sinkEffects: effects.size, outbox: 'sent' };
  });
});
await save('core', { sqlite });
