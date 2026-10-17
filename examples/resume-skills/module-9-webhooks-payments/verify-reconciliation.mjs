import { openStore } from './store.mjs';
import { reconcilePayment } from './reconcile.mjs';
import { endpoints, orders, fixtureEvent } from './fixtures.mjs';
import { receive, sign } from './webhook.mjs';
import { assert, check, rejected, save } from './checks.mjs';
const store = openStore(':memory:'); store.seed(orders);
const payment = fixtureEvent().payload.payment.entity;
const reconcile = fetchPayment => reconcilePayment({
  endpointId: 'alpha', endpoints, store, paymentId: payment.id, fetchPayment,
});
try {
  await check('provider lookup timeout leaves outcome unresolved and local balance unchanged', async () => {
    await assert.rejects(() => reconcile(async () => { throw new Error('provider timeout'); }), /provider timeout/);
    assert.equal(store.snapshot().ledger.length, 0); assert.equal(store.snapshot().inbox.length, 0);
    return { knownPaymentFailure: false, ledgerRows: 0 };
  });
  await check('account-bound lookup repairs missing captured webhook', async () => {
    const result = await reconcile(async () => ({ accountId: 'acc_alpha', payment }));
    assert.equal(result.reason, 'granted');
    assert.equal(store.snapshot().balances[0].credits, 100);
    return { reason: result.reason, credits: 100 };
  });
  await check('repeated observation and later real webhook share business invariant', async () => {
    await reconcile(async () => ({ accountId: 'acc_alpha', payment }));
    const raw = Buffer.from(JSON.stringify(fixtureEvent()));
    receive({ endpointId: 'alpha', endpoints, store, raw, signature: sign(raw, endpoints.alpha.secrets[0]), eventId: 'delayed-webhook' });
    store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
    return { ledgerRows: 1, credits: 100 };
  });
  await check('wrong provider account rejected before persistence', async () =>
    rejected(() => reconcile(async () => ({ accountId: 'acc_beta', payment })), 502, 'provider_account_mismatch'));
  await check('wrong provider payment ID rejected before persistence', async () =>
    rejected(() => reconcile(async () => ({ accountId: 'acc_alpha', payment: { ...payment, id: 'another' } })), 502, 'provider_payment_mismatch'));
  await check('unhandled provider state is unresolved rather than a grant', async () => {
    const result = await reconcile(async () => ({ accountId: 'acc_alpha', payment: { ...payment, status: 'created' } }));
    assert.equal(result.outcome, 'unresolved'); assert.equal(store.snapshot().ledger.length, 1);
    return { outcome: 'unresolved', ledgerRows: 1 };
  });
} finally { store.close(); }
await save('reconciliation');
