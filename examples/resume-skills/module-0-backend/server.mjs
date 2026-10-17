import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export function createDemoServer({ trace = () => {} } = {}) {
  // Process memory, not a database. Each new server starts with the same seed.
  const products = new Map([
    [7, { id: 7, name: 'Notebook', unitPricePaise: 25000, stock: 4 }],
  ]);

  function findProduct(rawId) {
    if (!/^[1-9][0-9]*$/.test(rawId ?? '')) {
      return { status: 400, error: 'invalid_product_id' };
    }
    const id = Number(rawId);
    if (!Number.isSafeInteger(id)) {
      return { status: 400, error: 'invalid_product_id' };
    }
    const product = products.get(id);
    return product
      ? { product }
      : { status: 404, error: 'product_not_found' };
  }

  return createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    trace('receive ' + req.method + ' ' + url.pathname);
    function send(status, data, headers = {}) {
      res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
        ...headers,
      });
      res.end(JSON.stringify(data));
      trace('respond ' + status);
    }

    const productMatch = /^\/api\/products\/([^/]+)$/.exec(url.pathname);
    const knownRoute = url.pathname === '/health' ||
      url.pathname === '/api/quote' || productMatch;
    if (!knownRoute) return send(404, { error: 'route_not_found' });
    if (req.method !== 'GET') {
      return send(405, { error: 'method_not_allowed' }, { Allow: 'GET' });
    }
    if (url.pathname === '/health') return send(200, { ok: true });

    trace('route ' + (productMatch ? 'product' : 'quote'));
    const found = findProduct(productMatch ? productMatch[1] : url.searchParams.get('productId'));
    if (found.error) return send(found.status, { error: found.error });
    trace('repository product=' + found.product.id);
    if (productMatch) return send(200, found.product);

    const rawQuantity = url.searchParams.get('quantity');
    if (!/^[1-9][0-9]*$/.test(rawQuantity ?? '')) {
      return send(400, { error: 'invalid_quantity' });
    }
    const quantity = Number(rawQuantity);
    if (!Number.isSafeInteger(quantity)) {
      return send(400, { error: 'invalid_quantity' });
    }
    if (quantity > found.product.stock) {
      return send(409, { error: 'insufficient_stock' });
    }
    // Price comes from our stored record. A client-supplied price is not used.
    const totalPaise = found.product.unitPricePaise * quantity;
    trace('service totalPaise=' + totalPaise);
    return send(200, {
      productId: found.product.id, quantity, totalPaise,
      currency: 'INR', reserved: false,
    });
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const server = createDemoServer({ trace: console.log });
  server.listen(3100, '127.0.0.1', () => {
    console.log('Demo listening at http://127.0.0.1:3100');
  });
}
