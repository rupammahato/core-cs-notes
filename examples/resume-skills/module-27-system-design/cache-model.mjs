import { routeKey } from './ring.mjs';

export class CacheModel {
  constructor(ring, sources, now, ttlMs = 100) {
    this.ring = ring; this.sources = sources; this.now = now; this.ttlMs = ttlMs;
    this.shards = new Map(ring.ids.map(id => [id, new Map()]));
    this.hits = 0; this.misses = 0;
  }

  get(tenant, key) {
    const canonical = routeKey(tenant, key), source = this.sources.get(canonical);
    if (!source || source.deleted) return null;
    const owner = this.ring.owner(canonical);
    if (!this.shards.has(owner)) this.shards.set(owner, new Map());
    const shard = this.shards.get(owner), cached = shard.get(canonical);
    // This controlled model consults canonical memory on every lookup.
    if (cached && cached.revision === source.revision && cached.expiresAt > this.now()) {
      this.hits++; return { ...cached, owner, hit: true };
    }
    this.misses++;
    const value = { text: source.text, revision: source.revision, expiresAt: this.now() + this.ttlMs };
    shard.set(canonical, value);
    return { ...value, owner, hit: false };
  }
}
