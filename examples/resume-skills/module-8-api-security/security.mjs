export class ApiError extends Error {
  constructor(status, code, headers = {}) {
    super(code); Object.assign(this, { status, code, headers });
  }
}
export const fail = (status, code, headers) => { throw new ApiError(status, code, headers); };
export const roles = new Set(['viewer', 'editor', 'admin']);
export function allowed(role, subject, action, row) {
  if (!roles.has(role)) return false;
  if (action === 'create') return role === 'editor' || role === 'admin';
  if (!row) return false;
  if (action === 'read') return role === 'admin' || row.visibility === 'tenant' || row.ownerId === subject;
  if (action === 'update' || action === 'delete')
    return role === 'admin' || (role === 'editor' && row.ownerId === subject);
  return false;
}
export function writable(input, partial = false) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail(400, 'invalid_document');
  const keys = Object.keys(input);
  if (keys.some(key => !['title', 'visibility'].includes(key))) fail(400, 'unknown_field');
  if (partial && !keys.length) fail(400, 'empty_patch');
  const result = {};
  if (!partial || Object.hasOwn(input, 'title')) {
    if (typeof input.title !== 'string' || !input.title.trim() || input.title.trim().length > 80)
      fail(400, 'invalid_title');
    result.title = input.title.trim();
  }
  if (Object.hasOwn(input, 'visibility')) {
    if (!['private', 'tenant'].includes(input.visibility)) fail(400, 'invalid_visibility');
    result.visibility = input.visibility;
  } else if (!partial) result.visibility = 'private';
  return result;
}
export function safeFilename(name) {
  if (typeof name !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,59}\.txt$/.test(name))
    fail(400, 'invalid_filename');
  return name;
}
export function textContent(bytes) {
  if (!(bytes instanceof Uint8Array)) fail(400, 'invalid_text');
  if (bytes.byteLength > 1024) fail(413, 'body_too_large');
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { fail(400, 'invalid_utf8'); }
  if (text.includes('\0')) fail(400, 'invalid_text');
  return text;
}
export function escapeHtmlText(value) {
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}
export function createBudget({ now = Date.now, limit = 3, windowMs = 10_000 } = {}) {
  const buckets = new Map();
  return (tenant, subject) => {
    const time = now(), window = Math.floor(time / windowMs);
    const key = JSON.stringify([tenant, subject, 'import']);
    let bucket = buckets.get(key);
    if (!bucket || bucket.window !== window) buckets.set(key, bucket = { window, used: 0 });
    if (bucket.used >= limit) fail(429, 'import_rate_limited', {
      'Retry-After': String(Math.max(1, Math.ceil(((window + 1) * windowMs - time) / 1000))),
    });
    bucket.used++;
  };
}
