import { Ring } from './ring.mjs';

export class Pool {
  constructor(backends, { strategy = 'hash', failures = 3, successes = 2 } = {}) {
    if (!['hash', 'round-robin', 'least-inflight'].includes(strategy)) throw new Error('Bad strategy');
    if (![failures, successes].every(v => Number.isInteger(v) && v > 0)) throw new Error('Bad health thresholds');
    this.nodes = [...backends].sort((a, b) => a.id.localeCompare(b.id)).map(b => {
      const origin = new URL(b.origin);
      if (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1' || origin.pathname !== '/' || origin.search || origin.username || origin.password) throw new Error('Fixture upstream must be loopback');
      return { ...b, healthy: true, draining: false, active: 0, failed: 0, succeeded: 0 };
    });
    this.ring = new Ring(this.nodes.map(n => n.id));
    this.strategy = strategy;
    this.failureThreshold = failures;
    this.successThreshold = successes;
    this.cursor = 0;
  }

  eligible(node) { return node.healthy && !node.draining; }

  choose(key) {
    const eligible = this.nodes.filter(n => this.eligible(n));
    if (!eligible.length) return null;
    if (this.strategy === 'round-robin') return eligible[this.cursor++ % eligible.length];
    if (this.strategy === 'least-inflight') return eligible.reduce((best, node) => node.active < best.active ? node : best);
    const candidates = this.ring.candidates(key);
    return candidates.map(id => this.nodes.find(n => n.id === id)).find(n => this.eligible(n));
  }

  observe(id, ok) {
    const node = this.nodes.find(n => n.id === id);
    if (!node) throw new Error('Unknown member');
    if (ok) {
      node.failed = 0;
      if (++node.succeeded >= this.successThreshold) node.healthy = true;
    } else {
      node.succeeded = 0;
      if (++node.failed >= this.failureThreshold) node.healthy = false;
    }
    return node.healthy;
  }

  drain(id, draining = true) {
    const node = this.nodes.find(n => n.id === id);
    if (!node) throw new Error('Unknown member');
    node.draining = draining;
  }
}
