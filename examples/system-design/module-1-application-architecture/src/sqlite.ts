import { DatabaseSync } from 'node:sqlite';
import { createHash, randomUUID } from 'node:crypto';
import { RuleError, type NotesRepository, type Note, type Principal, type Payload, type Trace } from './notes.js';

export class SqliteNotes implements NotesRepository {
  private readonly db: DatabaseSync;
  constructor(path: string, private readonly idFactory: () => string = randomUUID,
              private readonly afterInsert: () => void = () => {}) {
    this.db = new DatabaseSync(path);
    this.db.exec(`PRAGMA foreign_keys=ON; PRAGMA busy_timeout=2000;
      CREATE TABLE IF NOT EXISTS notes (
        tenant TEXT NOT NULL, owner TEXT NOT NULL, id TEXT NOT NULL,
        title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
        content TEXT NOT NULL CHECK(length(CAST(content AS BLOB)) <= 4096),
        revision INTEGER NOT NULL CHECK(revision > 0), PRIMARY KEY(tenant,id)
      ) STRICT;
      CREATE TABLE IF NOT EXISTS operations (
        tenant TEXT NOT NULL, owner TEXT NOT NULL, operation TEXT NOT NULL,
        fingerprint TEXT NOT NULL, note_id TEXT NOT NULL, response TEXT NOT NULL,
        PRIMARY KEY(tenant,owner,operation),
        FOREIGN KEY(tenant,note_id) REFERENCES notes(tenant,id)
      ) STRICT;`);
  }
  private transaction<T>(trace: Trace, work: () => T): T {
    this.db.exec('BEGIN IMMEDIATE');
    trace('repository.transaction.begin');
    try {
      const result = work();
      this.db.exec('COMMIT');
      trace('repository.transaction.commit');
      return result;
    } catch (error) {
      this.db.exec('ROLLBACK');
      trace('repository.transaction.rollback');
      throw error;
    }
  }
  create(who: Principal, operation: string, input: Payload, trace: Trace) {
    const fingerprint = createHash('sha256').update(JSON.stringify([input.title, input.content])).digest('hex');
    return this.transaction(trace, () => {
      const previous = this.db.prepare(`SELECT fingerprint,response FROM operations
        WHERE tenant=? AND owner=? AND operation=?`).get(who.tenant, who.owner, operation);
      if (previous) {
        if (previous.fingerprint !== fingerprint) throw new RuleError('conflict');
        trace('repository.operation.replayed');
        return { note: JSON.parse(previous.response as string) as Note, replayed: true };
      }
      const note: Note = { id: this.idFactory(), ...input, revision: 1 };
      this.db.prepare('INSERT INTO notes VALUES(?,?,?,?,?,?)')
        .run(who.tenant, who.owner, note.id, note.title, note.content, note.revision);
      trace('repository.note.inserted');
      this.afterInsert(); // Owned test fault; no HTTP switch exposes it.
      this.db.prepare('INSERT INTO operations VALUES(?,?,?,?,?,?)')
        .run(who.tenant, who.owner, operation, fingerprint, note.id, JSON.stringify(note));
      trace('repository.operation.saved');
      return { note, replayed: false };
    });
  }
  get(who: Principal, id: string, trace: Trace): Note {
    const row = this.db.prepare(`SELECT id,title,content,revision FROM notes
      WHERE tenant=? AND owner=? AND id=?`).get(who.tenant, who.owner, id);
    trace('repository.note.scoped_read');
    if (!row) throw new RuleError('missing');
    return { id: row.id as string, title: row.title as string, content: row.content as string, revision: row.revision as number };
  }
  replace(who: Principal, id: string, revision: number, input: Payload, trace: Trace): Note {
    return this.transaction(trace, () => {
      const result = this.db.prepare(`UPDATE notes SET title=?,content=?,revision=revision+1
        WHERE tenant=? AND owner=? AND id=? AND revision=?`)
        .run(input.title, input.content, who.tenant, who.owner, id, revision);
      if (result.changes === 0) {
        this.get(who, id, trace); // Invisible and absent remain the same outcome.
        throw new RuleError('stale');
      }
      trace('repository.note.replaced');
      return this.get(who, id, trace);
    });
  }
  close(): void { this.db.close(); }
}
