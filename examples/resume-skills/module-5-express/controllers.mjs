export function createProductControllers(service) {
  return {
    async getProduct(request, response) {
      response.locals.trace.push('controller');
      const product = await service.getProduct(response.locals.productId, response.locals.trace);
      response.json({ product, requestId: response.locals.requestId });
    },
    async quote(request, response) {
      response.locals.trace.push('controller');
      const quote = await service.quote(response.locals.quoteInput, response.locals.trace);
      response.json({ quote, requestId: response.locals.requestId });
    },
  };
}
