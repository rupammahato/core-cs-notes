import express, { type RequestHandler } from 'express';

type QuoteInput = { productId: number; quantity: number };
type Reply = { input: QuoteInput } | { error: string };
type Locals = { quoteInput?: QuoteInput };
type Handler = RequestHandler<Record<string, string>, Reply, unknown, Record<string, unknown>, Locals>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export const validate: Handler = (request, response, next) => {
  const body = request.body; // unknown, not an already-trusted DTO.
  if (!isRecord(body) ||
      Object.keys(body).some(key => key !== 'productId' && key !== 'quantity')) {
    response.status(400).json({ error: 'invalid_body' });
    return;
  }
  const { productId, quantity } = body;
  if (typeof productId !== 'number' || !Number.isSafeInteger(productId) || productId < 1 ||
      typeof quantity !== 'number' || !Number.isSafeInteger(quantity) ||
      quantity < 1 || quantity > 10) {
    response.status(400).json({ error: 'invalid_values' });
    return;
  }
  response.locals.quoteInput = { productId, quantity };
  next();
};

export const respond: Handler = (request, response) => {
  const input = response.locals.quoteInput;
  if (!input) {
    response.status(500).json({ error: 'validation_missing' });
    return;
  }
  response.json({ input });
};

export function createTypedApp() {
  const app = express();
  app.post('/typed', express.json({ limit: '1kb' }), validate, respond);
  return app;
}
