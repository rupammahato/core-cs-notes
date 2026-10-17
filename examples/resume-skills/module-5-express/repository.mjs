export function createProductRepository() {
  const products = new Map([
    [7, { id: 7, name: 'Keyboard', unitPricePaise: 25000, stock: 4, internalCostPaise: 13000 }],
    [8, { id: 8, name: 'Mouse', unitPricePaise: 15000, stock: 0, internalCostPaise: 7000 }],
  ]);
  return {
    async findById(id, trace = []) {
      trace.push('repository');
      await Promise.resolve(); // Simulated async contract, not database I/O.
      const row = products.get(id);
      return row ? { ...row } : undefined;
    },
  };
}
