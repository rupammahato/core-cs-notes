import { DatabaseSync } from 'node:sqlite';
import { fail } from './webhook.mjs';

export function openStore(filename, { onPhase = () => {} } = {}) {
  if (typeof filename !== 'string' || !filename)
    throw new TypeError('Supply a database path or explicit :memory: for tests.');
  const db = new DatabaseSync(filename);
  db.exec(`
    PRAGMA foreign_keys = ON;
    PRAGMA journal_mode = DELETE;
    PRAGMA synchronous = FULL;
    PRAGMA busy_timeout = 5000;
    CREATE TABLE IF NOT EXISTS orders (
      tenant TEXT NOT NULL, local_id TEXT NOT NULL, endpoint TEXT NOT NULL,
      provider_id TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount > 0),
      currency TEXT NOT NULL, credits INTEGER NOT NULL CHECK(credits > 0),
      state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','paid')),
      PRIMARY KEY(tenant, local_id), UNIQUE(endpoint, provider_id)
    );
    CREATE TABLE IF NOT EXISTS inbox (
      endpoint TEXT NOT NULL, event_id TEXT NOT NULL, raw_hash TEXT NOT NULL,
      payload TEXT NOT NULL, state TEXT NOT NULL, reason TEXT,
      PRIMARY KEY(endpoint, event_id)
    );
    CREATE TABLE IF NOT EXISTS payments (
      endpoint TEXT NOT NULL, payment_id TEXT NOT NULL,
      provider_order_id TEXT NOT NULL, amount INTEGER NOT NULL,
      currency TEXT NOT NULL, state TEXT NOT NULL,
      PRIMARY KEY(endpoint, payment_id)
    );
    CREATE TABLE IF NOT EXISTS ledger (
      tenant TEXT NOT NULL, local_order_id TEXT NOT NULL,
      endpoint TEXT NOT NULL, payment_id TEXT NOT NULL,
      credits INTEGER NOT NULL CHECK(credits > 0), kind TEXT NOT NULL,
      PRIMARY KEY(tenant, local_order_id, kind),
      UNIQUE(endpoint, payment_id, kind),
      FOREIGN KEY(tenant, local_order_id) REFERENCES orders(tenant, local_id)
    );
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
      attempts INTEGER NOT NULL DEFAULT 0
    );
  `);
  const one = (sql, ...args) => db.prepare(sql).get(...args);
  const all = (sql, ...args) => db.prepare(sql).all(...args);
  const run = (sql, ...args) => db.prepare(sql).run(...args);
  function transaction(operation) {
    db.exec('BEGIN IMMEDIATE');
    try {
      const result = operation();
      db.exec('COMMIT');
      return result;
    } catch (error) {
      try { db.exec('ROLLBACK'); } catch { /* preserve the original failure */ }
      throw error;
    }
  }
  function seed(items) {
    for (const item of items) run(`
      INSERT OR IGNORE INTO orders(tenant,local_id,endpoint,provider_id,amount,currency,credits)
      VALUES(?,?,?,?,?,?,?)
    `, item.tenant, item.localId, item.endpoint, item.providerId, item.amount, item.currency, item.credits);
  }
  function accept(endpoint, eventId, rawHash, event) {
    const accepted = transaction(() => {
      const prior = one('SELECT raw_hash,state FROM inbox WHERE endpoint=? AND event_id=?', endpoint, eventId);
      if (prior) {
        if (prior.raw_hash !== rawHash) fail(409, 'event_id_conflict');
        return { accepted: true, duplicate: true, state: prior.state };
      }
      onPhase('before-inbox-insert');
      run('INSERT INTO inbox(endpoint,event_id,raw_hash,payload,state) VALUES(?,?,?,?,?)',
        endpoint, eventId, rawHash, JSON.stringify(event), event.ignored ? 'ignored' : 'pending');
      return { accepted: true, duplicate: false, state: event.ignored ? 'ignored' : 'pending' };
    });
    onPhase('after-inbox-commit');
    return accepted;
  }
  function processOne(endpoint, eventId) {
    const result = transaction(() => {
      const receipt = one('SELECT * FROM inbox WHERE endpoint=? AND event_id=?', endpoint, eventId);
      if (!receipt || receipt.state !== 'pending') return { outcome: receipt?.state ?? 'missing' };
      const event = JSON.parse(receipt.payload);
      const finish = (state, reason) => {
        run('UPDATE inbox SET state=?,reason=? WHERE endpoint=? AND event_id=?', state, reason, endpoint, eventId);
        return { outcome: state, reason };
      };
      const order = one('SELECT * FROM orders WHERE endpoint=? AND provider_id=?', endpoint, event.providerOrderId);
      if (!order) return finish('review', 'unknown_order');
      if (order.amount !== event.amount || order.currency !== event.currency)
        return finish('review', 'amount_or_currency_mismatch');
      const prior = one('SELECT * FROM payments WHERE endpoint=? AND payment_id=?', endpoint, event.paymentId);
      if (prior && (prior.provider_order_id !== event.providerOrderId ||
          prior.amount !== event.amount || prior.currency !== event.currency))
        return finish('review', 'payment_identity_conflict');
      // Captured is absorbing only for this deliberately narrow payment model.
      const state = prior?.state === 'captured' || event.status === 'captured' ? 'captured'
        : prior?.state === 'failed' || event.status === 'failed' ? 'failed' : 'authorized';
      run(`INSERT INTO payments(endpoint,payment_id,provider_order_id,amount,currency,state)
        VALUES(?,?,?,?,?,?) ON CONFLICT(endpoint,payment_id) DO UPDATE SET state=excluded.state`,
      endpoint, event.paymentId, event.providerOrderId, event.amount, event.currency, state);
      if (event.status !== 'captured') return finish('processed', 'no_capture_grant');
      const granted = one("SELECT * FROM ledger WHERE tenant=? AND local_order_id=? AND kind='purchase'",
        order.tenant, order.local_id);
      if (granted) {
        if (granted.payment_id !== event.paymentId) return finish('review', 'order_already_funded');
        return finish('processed', 'already_granted');
      }
      run("INSERT INTO ledger(tenant,local_order_id,endpoint,payment_id,credits,kind) VALUES(?,?,?,?,?,'purchase')",
        order.tenant, order.local_id, endpoint, event.paymentId, order.credits);
      onPhase('after-ledger-write');
      run("UPDATE orders SET state='paid' WHERE tenant=? AND local_id=?", order.tenant, order.local_id);
      const notificationId = JSON.stringify(['credit-granted', order.tenant, order.local_id]);
      run('INSERT INTO outbox(id,payload) VALUES(?,?)', notificationId, JSON.stringify({
        tenant: order.tenant, orderId: order.local_id, credits: order.credits,
      }));
      const completed = finish('processed', 'granted');
      onPhase('before-effect-commit');
      return completed;
    });
    onPhase('after-effect-commit');
    return result;
  }
  function processNext() {
    const row = one("SELECT endpoint,event_id FROM inbox WHERE state='pending' ORDER BY rowid LIMIT 1");
    return row ? processOne(row.endpoint, row.event_id) : { outcome: 'idle' };
  }
  async function dispatchOne(send, { afterSend = () => {} } = {}) {
    const row = one("SELECT * FROM outbox WHERE state='pending' ORDER BY rowid LIMIT 1");
    if (!row) return { outcome: 'idle' };
    run('UPDATE outbox SET attempts=attempts+1 WHERE id=?', row.id);
    await send({ id: row.id, payload: JSON.parse(row.payload) });
    await afterSend();
    run("UPDATE outbox SET state='sent' WHERE id=?", row.id);
    return { outcome: 'sent', id: row.id };
  }
  function snapshot() {
    return {
      orders: all('SELECT * FROM orders ORDER BY tenant,local_id'),
      inbox: all('SELECT endpoint,event_id,state,reason FROM inbox ORDER BY endpoint,event_id'),
      payments: all('SELECT * FROM payments ORDER BY endpoint,payment_id'),
      ledger: all('SELECT * FROM ledger ORDER BY tenant,local_order_id'),
      outbox: all('SELECT * FROM outbox ORDER BY id'),
      balances: all('SELECT tenant,SUM(credits) AS credits FROM ledger GROUP BY tenant ORDER BY tenant'),
    };
  }
  return {
    seed, accept, processOne, processNext, dispatchOne, snapshot,
    sqlite: () => one('SELECT sqlite_version() AS version').version,
    configuration: () => ({ journal: one('PRAGMA journal_mode').journal_mode,
      synchronous: one('PRAGMA synchronous').synchronous, foreignKeys: one('PRAGMA foreign_keys').foreign_keys }),
    close: () => db.close(),
  };
}
