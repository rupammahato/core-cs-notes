import { AppError } from './errors.mjs';

export function createProductService(repository) {
  async function find(id, trace) {
    trace.push('service');
    const row = await repository.findById(id, trace);
    if (!row) throw new AppError(404, 'product_not_found');
    return row;
  }
  return {
    async getProduct(id, trace = []) {
      const row = await find(id, trace);
      return { id: row.id, name: row.name, unitPricePaise: row.unitPricePaise, stock: row.stock };
    },
    async quote(input, trace = []) {
      const row = await find(input.productId, trace);
      if (input.quantity > row.stock) throw new AppError(409, 'insufficient_stock');
      const totalPaise = row.unitPricePaise * input.quantity;
      if (!Number.isSafeInteger(totalPaise)) throw new Error('invalid stored price calculation');
      return {
        productId: row.id, quantity: input.quantity,
        unitPricePaise: row.unitPricePaise, totalPaise,
      };
    },
  };
}
