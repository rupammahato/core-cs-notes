import { createHash } from 'node:crypto';

export const digest = value => createHash('sha256').update(value).digest();
export const hash64 = value => digest(value).readBigUInt64BE(0);

export class Ring {
  constructor(ids, replicas = 128) {
    if (!Number.isInteger(replicas) || replicas < 1 || replicas > 1024) throw new Error('Bad replica count');
    if (!ids.length || new Set(ids).size !== ids.length || ids.some(id => !/^[a-z0-9-]{1,40}$/.test(id))) throw new Error('Bad members');
    this.ids = [...ids].sort();
    this.replicas = replicas;
    this.tokens = this.ids.flatMap(id => Array.from({ length: replicas }, (_, replica) => ({
      point: hash64(JSON.stringify([id, replica])), id, replica,
    }))).sort((a, b) => a.point < b.point ? -1 : a.point > b.point ? 1 : a.id.localeCompare(b.id) || a.replica - b.replica);
    this.version = digest(JSON.stringify({ hash: 'sha256-first64be', ids: this.ids, replicas })).toString('hex').slice(0, 12);
  }

  locate(point) {
    let lo = 0, hi = this.tokens.length;
    while (lo < hi) {
      const mid = (lo + hi) >>> 1;
      if (this.tokens[mid].point < point) lo = mid + 1; else hi = mid;
    }
    return lo === this.tokens.length ? 0 : lo;
  }

  candidates(key) {
    if (typeof key !== 'string' || !key.length) throw new Error('Bad routing key');
    const start = this.locate(hash64(key)), seen = new Set(), result = [];
    for (let offset = 0; offset < this.tokens.length && result.length < this.ids.length; offset++) {
      const id = this.tokens[(start + offset) % this.tokens.length].id;
      if (!seen.has(id)) { seen.add(id); result.push(id); }
    }
    return result;
  }

  owner(key) { return this.tokens[this.locate(hash64(key))].id; }
}

export const routeKey = (tenant, key) => JSON.stringify([tenant, key]);

export function movement(keys, before, after) {
  const moved = keys.filter(key => before.owner(key) !== after.owner(key)).length;
  return { keys: keys.length, moved, fraction: moved / keys.length };
}
