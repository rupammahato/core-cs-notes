from contextlib import closing
import json
import sqlite3

with closing(sqlite3.connect(':memory:')) as db:
    db.execute('CREATE TABLE identities(key TEXT UNIQUE)')
    with db:
        db.executemany('INSERT INTO identities VALUES (?)', [(None,), (None,), ('x',)])
    rejected = False
    try:
        with db:
            db.execute("INSERT INTO identities VALUES ('x')")
    except sqlite3.IntegrityError:
        rejected = True
    print(json.dumps({'rows': db.execute('SELECT COUNT(*) FROM identities').fetchone()[0], 'null_rows': db.execute('SELECT COUNT(*) FROM identities WHERE key IS NULL').fetchone()[0], 'duplicate_rejected': rejected}))
