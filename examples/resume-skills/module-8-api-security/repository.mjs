const key = (tenant, id) => JSON.stringify([tenant, id]);
const clone = row => row && { ...row };

export function createRepository() {
  const rows = new Map();
  const members = new Map([
    ['alpha', new Map([['alice', 'editor'], ['bob', 'viewer'], ['dana', 'viewer']])],
    ['beta', new Map([['carol', 'admin'], ['dana', 'admin']])],
  ]);
  const initial = [
    { tenantId: 'alpha', id: 1, ownerId: 'alice', title: 'Alpha private', visibility: 'private' },
    { tenantId: 'alpha', id: 2, ownerId: 'bob', title: 'Alpha shared', visibility: 'tenant' },
    { tenantId: 'beta', id: 1, ownerId: 'carol', title: 'Beta shared', visibility: 'tenant' },
    { tenantId: 'beta', id: 2, ownerId: 'carol', title: 'Beta private', visibility: 'private' },
  ];
  for (const row of initial) rows.set(key(row.tenantId, row.id), {
    ...row, version: 1, content: row.title, internalNote: 'PRIVATE-OPERATOR-NOTE',
  });
  const next = new Map([['alpha', 3], ['beta', 3]]);
  return {
    role: (tenant, subject) => members.get(tenant)?.get(subject),
    get: (tenant, id) => clone(rows.get(key(tenant, id))),
    list: tenant => [...rows.values()].filter(row => row.tenantId === tenant).map(clone),
    put: row => { rows.set(key(row.tenantId, row.id), clone(row)); },
    remove: (tenant, id) => rows.delete(key(tenant, id)),
    create: (tenant, subject, input) => {
      const row = {
        tenantId: tenant, id: next.get(tenant), ownerId: subject,
        ...input, version: 1, internalNote: 'PRIVATE-OPERATOR-NOTE',
      };
      next.set(tenant, row.id + 1);
      rows.set(key(tenant, row.id), clone(row));
      return clone(row);
    },
    // Test-only administrative seam, never exposed as an HTTP endpoint.
    setRole: (tenant, subject, role) => {
      if (role === null) members.get(tenant)?.delete(subject);
      else members.get(tenant)?.set(subject, role);
    },
  };
}
