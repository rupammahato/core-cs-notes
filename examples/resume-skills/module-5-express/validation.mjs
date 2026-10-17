import { AppError } from './errors.mjs';

export function parseProductId(value) {
  if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) {
    throw new AppError(400, 'invalid_product_id');
  }
  const id = Number(value);
  if (!Number.isSafeInteger(id)) throw new AppError(400, 'invalid_product_id');
  return id;
}

export function parseQuote(input) {
  if (typeof input !== 'object' || input === null || Array.isArray(input)) {
    throw new AppError(400, 'invalid_body');
  }
  if (Object.keys(input).some(key => key !== 'productId' && key !== 'quantity')) {
    throw new AppError(400, 'unknown_fields');
  }
  const { productId, quantity } = input;
  if (typeof productId !== 'number' || !Number.isSafeInteger(productId) || productId < 1) {
    throw new AppError(400, 'invalid_product_id');
  }
  if (typeof quantity !== 'number' || !Number.isSafeInteger(quantity) ||
      quantity < 1 || quantity > 10) {
    throw new AppError(400, 'invalid_quantity');
  }
  return { productId, quantity };
}
