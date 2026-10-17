import type { RequestHandler } from 'express';

const unsafe: RequestHandler<Record<string, string>, unknown, unknown> = (request, response) => {
  response.json(request.body.quantity);
};
