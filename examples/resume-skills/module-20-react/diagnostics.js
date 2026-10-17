// Test-only diagnostics: event handlers/effects record events, never component render.
export const events = [];
export const subscriptions = new Set();
export function record(type, fields = {}) { events.push({ type, ...fields }); }
