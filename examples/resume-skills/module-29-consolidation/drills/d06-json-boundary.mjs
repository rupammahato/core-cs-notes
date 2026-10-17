const input = JSON.parse('{"role":"admin","limit":"10"}');
console.log(JSON.stringify({ role: input.role, limitType: typeof input.limit, limitPlusOne: input.limit + 1 }));
