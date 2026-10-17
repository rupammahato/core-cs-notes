const effects = [];
const a = Promise.resolve().then(() => { effects.push('first'); return 1; });
const b = Promise.resolve().then(() => { throw new Error('fail'); });
const c = Promise.resolve().then(() => { effects.push('third'); return 3; });
try { await Promise.all([a, b, c]); }
catch (error) { console.log(JSON.stringify({ error: error.message, effects })); }
