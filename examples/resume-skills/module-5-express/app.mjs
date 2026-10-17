import express from 'express';
import { randomUUID } from 'node:crypto';
import { AppError, publicError } from './errors.mjs';
import { parseProductId, parseQuote } from './validation.mjs';
import { createProductRepository } from './repository.mjs';
import { createProductService } from './service.mjs';
import { createProductControllers } from './controllers.mjs';

export function createApp({ repository = createProductRepository(), onComplete = () => {} } = {}) {
  const app = express();
  app.disable('x-powered-by');
  app.set('query parser', 'simple');

  app.use((request, response, next) => {
    response.locals.requestId = randomUUID();
    response.locals.trace = ['request'];
    response.set('X-Request-Id', response.locals.requestId);
    response.once('finish', () => onComplete({
      requestId: response.locals.requestId, status: response.statusCode,
      path: request.originalUrl, trace: [...response.locals.trace],
    }));
    next();
  });

  app.get('/health', (request, response) => {
    response.locals.trace.push('health');
    response.json({ status: 'ok', requestId: response.locals.requestId });
  });

  const controller = createProductControllers(createProductService(repository));
  const router = express.Router();
  router.use((request, response, next) => {
    response.locals.trace.push('router');
    next();
  });

  router.get('/products/:productId', (request, response, next) => {
    response.locals.trace.push('validate-id');
    response.locals.productId = parseProductId(request.params.productId);
    next();
  }, controller.getProduct);

  router.post('/quotes', (request, response, next) => {
    response.locals.trace.push('media-type');
    if (!request.get('content-type') || request.is('application/json') === false) {
      throw new AppError(415, 'json_required');
    }
    next();
  }, express.json({ limit: '1kb', strict: true, inflate: false }),
  (request, response, next) => {
    response.locals.trace.push('parsed', 'validate-body');
    response.locals.quoteInput = parseQuote(request.body);
    next();
  }, controller.quote);

  // Explicit method policy for known routes; this also overrides automatic OPTIONS.
  router.all('/products/:productId', (request, response) => {
    response.set('Allow', 'GET, HEAD');
    throw new AppError(405, 'method_not_allowed');
  });
  router.all('/quotes', (request, response) => {
    response.set('Allow', 'POST');
    throw new AppError(405, 'method_not_allowed');
  });

  app.use('/api', router);
  app.use((request, response) => {
    response.locals.trace.push('not-found');
    response.status(404).json({ error: { code: 'route_not_found' }, requestId: response.locals.requestId });
  });

  app.use((error, request, response, next) => {
    response.locals.trace.push('error');
    if (response.headersSent) return next(error);
    const { status, code } = publicError(error);
    response.status(status).json({ error: { code }, requestId: response.locals.requestId });
  });
  return app;
}
