const values = [1, 2].map(async value => value * 2);
console.log(JSON.stringify({ firstIsPromise: values[0] instanceof Promise, resolved: await Promise.all(values) }));
