import { DatabaseSync } from 'node:sqlite';
import { assert, check, save } from './checks.mjs';

const db = new DatabaseSync(':memory:');
const sqlite = db.prepare('SELECT sqlite_version() AS version').get().version;
try {
  db.exec(`
    PRAGMA foreign_keys = ON;
    CREATE TABLE projects (
      tenant_id TEXT NOT NULL, id INTEGER NOT NULL,
      PRIMARY KEY (tenant_id, id)
    );
    CREATE TABLE documents (
      tenant_id TEXT NOT NULL, id INTEGER NOT NULL, project_id INTEGER NOT NULL,
      title TEXT NOT NULL, PRIMARY KEY (tenant_id, id),
      FOREIGN KEY (tenant_id, project_id) REFERENCES projects (tenant_id, id)
    );
    INSERT INTO projects VALUES ('alpha', 10), ('beta', 20);
    INSERT INTO documents VALUES
      ('alpha', 1, 10, 'Alpha private'), ('alpha', 2, 10, 'Alpha shared'),
      ('beta', 1, 20, 'Beta shared'), ('beta', 2, 20, 'Beta private');
  `);
  await check('composite identity distinguishes same ID across tenants', async () => {
    const query = db.prepare('SELECT title FROM documents WHERE tenant_id = ? AND id = ?');
    assert.equal(query.get('alpha', 1).title, 'Alpha private');
    assert.equal(query.get('beta', 1).title, 'Beta shared');
    return { alpha1: 'Alpha private', beta1: 'Beta shared' };
  });
  const payload = "' OR 1=1 --";
  await check('unsafe concatenation leaks rows in isolated training database', async () => {
    const query = "SELECT tenant_id, id FROM documents WHERE tenant_id = 'alpha' AND title = '" + payload + "'";
    const rows = db.prepare(query).all();
    assert.equal(rows.length, 4);
    assert.ok(rows.some(row => row.tenant_id === 'beta'));
    return { rows: rows.length, includesOtherTenant: true };
  });
  await check('bound value remains data rather than injected SQL', async () => {
    const rows = db.prepare('SELECT tenant_id, id FROM documents WHERE tenant_id = ? AND title = ?')
      .all('alpha', payload);
    assert.equal(rows.length, 0);
    return { rows: rows.length };
  });
  await check('parameterization alone does not add tenant authorization', async () => {
    const rows = db.prepare('SELECT tenant_id, id FROM documents WHERE id = ?').all(1);
    assert.equal(rows.length, 2);
    return { rows: rows.length, distinctTenants: rows.map(row => row.tenant_id).sort() };
  });
  await check('composite foreign key rejects cross-tenant parent', async () => {
    assert.throws(() => db.prepare('INSERT INTO documents VALUES (?, ?, ?, ?)').run('alpha', 3, 20, 'Bad relation'), error => /FOREIGN KEY constraint failed/.test(error.message));
    assert.equal(db.prepare('SELECT count(*) AS n FROM documents').get().n, 4);
    return { rejected: true, rowsRemain: 4 };
  });
  await check('allowed sort mapping rejects identifier injection', async () => {
    const sorts = new Map([['title', 'title'], ['id', 'id']]);
    const requested = 'title; DROP TABLE documents; --';
    assert.equal(sorts.has(requested), false);
    const column = sorts.get('title');
    const rows = db.prepare('SELECT id FROM documents WHERE tenant_id = ? ORDER BY ' + column + ', id').all('alpha');
    assert.deepEqual(rows.map(row => row.id), [1, 2]);
    return { rejectedSort: true, allowedSortIds: [1, 2] };
  });
} finally { db.close(); }
await save('sql', { sqlite, api: 'node:sqlite (experimental on recorded runtime)' });
