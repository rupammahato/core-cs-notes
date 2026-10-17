import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createDemoServer } from './server.mjs';

const trace = [];
const server = createDemoServer({ trace: (line) => trace.push(line) });
server.listen(0, '127.0.0.1');
await once(server, 'listening');
const base = 'http://127.0.0.1:' + server.address().port;
let checks = 0;
async function check(name, route, status, expected, options) {
  const response = await fetch(base + route, {
    ...options, signal: AbortSignal.timeout(5000),
  });
  assert.equal(response.status, status);
  assert.match(response.headers.get('content-type'), /^application\/json/);
  assert.deepEqual(await response.json(), expected);
  checks++;
  console.log('PASS ' + name + ' -> ' + status);
  return response;
}
const product = { id: 7, name: 'Notebook', unitPricePaise: 25000, stock: 4 };
try {
  await check('health', '/health', 200, { ok: true });
  await check('stored product', '/api/products/7', 200, product);
  await check('invalid ID', '/api/products/seven', 400, { error: 'invalid_product_id' });
  await check('unknown product', '/api/products/99', 404, { error: 'product_not_found' });
  await check('unknown route', '/api/missing', 404, { error: 'route_not_found' });
  const wrongMethod = await check('unsupported method', '/api/products/7', 405,
    { error: 'method_not_allowed' }, { method: 'POST' });
  assert.equal(wrongMethod.headers.get('allow'), 'GET');
  await check('missing quantity', '/api/quote?productId=7', 400, { error: 'invalid_quantity' });
  await check('zero quantity', '/api/quote?productId=7&quantity=0', 400, { error: 'invalid_quantity' });
  await check('fractional quantity', '/api/quote?productId=7&quantity=1.5', 400, { error: 'invalid_quantity' });
  await check('unsafe integer ID', '/api/products/9007199254740993', 400,
    { error: 'invalid_product_id' });
  await check('unavailable quantity', '/api/quote?productId=7&quantity=5', 409,
    { error: 'insufficient_stock' });
  trace.length = 0;
  await check('forged price ignored', '/api/quote?productId=7&quantity=2&unitPricePaise=1', 200,
    { productId: 7, quantity: 2, totalPaise: 50000, currency: 'INR', reserved: false });
  assert.deepEqual(trace, [
    'receive GET /api/quote', 'route quote', 'repository product=7',
    'service totalPaise=50000', 'respond 200',
  ]);
  const quoteTrace = [...trace];
  await check('quote does not reserve stock', '/api/products/7', 200, product);
  console.log('TRACE ' + quoteTrace.join(' -> '));
  console.log('Verified ' + checks + ' HTTP cases; Node ' + process.version);
} finally {
  server.closeAllConnections();
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}
