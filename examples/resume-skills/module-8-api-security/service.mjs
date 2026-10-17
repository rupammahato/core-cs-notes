import { randomUUID } from 'node:crypto';
import { allowed, roles, writable, safeFilename, textContent, fail } from './security.mjs';

const view = row => ({
  id: row.id, title: row.title, ownerId: row.ownerId, visibility: row.visibility, version: row.version,
});
export function createDocumentService({ repository, beforeRead = async () => {}, beforeCommit = async () => {} }) {
  const cache = new Map();
  function context(principal, tenant, write = false) {
    const role = repository.role(tenant, principal.subject);
    if (!roles.has(role)) fail(404, 'not_found');
    if (!principal.scopes.has(write ? 'docs:write' : 'docs:read')) fail(403, 'scope_required');
    return role;
  }
  function visible(principal, tenant, id, write = false) {
    const role = context(principal, tenant, write);
    const row = repository.get(tenant, id);
    if (!row || !allowed(role, principal.subject, 'read', row)) fail(404, 'not_found');
    return { role, row };
  }
  function edit(principal, tenant, id, action, input) {
    const result = visible(principal, tenant, id, true);
    if (!allowed(result.role, principal.subject, action, result.row)) fail(403, 'forbidden');
    if (input && Object.hasOwn(input, 'visibility') && result.role !== 'admin')
      fail(403, 'visibility_change_forbidden');
    return result;
  }
  function mayCreate(principal, tenant) {
    const role = context(principal, tenant, true);
    if (!allowed(role, principal.subject, 'create')) fail(403, 'forbidden');
  }
  async function list(principal, tenant, { after = 0, limit = 2, query = '' } = {}) {
    if (!Number.isSafeInteger(after) || after < 0 || !Number.isSafeInteger(limit) || limit < 1 || limit > 5 ||
        typeof query !== 'string' || query.length > 80) fail(400, 'invalid_query');
    context(principal, tenant);
    await beforeRead({ tenant, subject: principal.subject, action: 'list' });
    const role = context(principal, tenant);
    const rows = repository.list(tenant)
      .filter(row => allowed(role, principal.subject, 'read', row))
      .filter(row => row.id > after && row.title.includes(query))
      .sort((a, b) => a.id - b.id);
    const items = rows.slice(0, limit).map(view);
    return { items, nextAfter: rows.length > limit ? items.at(-1).id : null };
  }
  async function get(principal, tenant, id, download = false) {
    context(principal, tenant);
    await beforeRead({ tenant, subject: principal.subject, action: 'get', id });
    const { row } = visible(principal, tenant, id);
    if (download) return { content: row.content, filename: 'document-' + row.id + '.txt' };
    const key = JSON.stringify([tenant, id, row.version]);
    // Always establish current membership/object permission before serving a cache hit.
    if (!cache.has(key)) cache.set(key, view(row));
    return { ...cache.get(key) };
  }
  async function create(principal, tenant, value) {
    mayCreate(principal, tenant);
    const input = writable(value);
    await beforeCommit({ tenant, subject: principal.subject, action: 'create' });
    mayCreate(principal, tenant);
    return view(repository.create(tenant, principal.subject, { ...input, content: input.title }));
  }
  async function update(principal, tenant, id, value, condition) {
    const input = writable(value, true);
    edit(principal, tenant, id, 'update', input);
    if (condition === undefined) fail(428, 'condition_required');
    await beforeCommit({ tenant, subject: principal.subject, action: 'update', id });
    const { row } = edit(principal, tenant, id, 'update', input);
    if (condition !== '"v' + row.version + '"') fail(412, 'stale_version');
    const updated = { ...row, ...input, version: row.version + 1 };
    repository.put(updated);
    return view(updated);
  }
  async function bulkDelete(principal, tenant, ids) {
    if (!Array.isArray(ids) || !ids.length || ids.length > 5 ||
        ids.some(id => !Number.isSafeInteger(id) || id < 1) || new Set(ids).size !== ids.length)
      fail(400, 'invalid_ids');
    const checkAll = () => ids.map(id => edit(principal, tenant, id, 'delete'));
    checkAll();
    await beforeCommit({ tenant, subject: principal.subject, action: 'bulk-delete' });
    checkAll();
    // All checks precede all effects; no await inside this local commit region.
    for (const id of ids) repository.remove(tenant, id);
  }
  async function importText(principal, tenant, filename, bytes) {
    mayCreate(principal, tenant);
    const title = safeFilename(filename), content = textContent(bytes);
    await beforeCommit({ tenant, subject: principal.subject, action: 'import' });
    mayCreate(principal, tenant);
    return view(repository.create(tenant, principal.subject, {
      title, content, visibility: 'private', storageKey: randomUUID(),
    }));
  }
  return { list, get, create, update, bulkDelete, importText, mayCreate };
}
