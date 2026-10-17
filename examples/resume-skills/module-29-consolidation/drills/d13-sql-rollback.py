from contextlib import closing
import json
import sqlite3

with closing(sqlite3.connect(':memory:')) as db:
    db.executescript('CREATE TABLE balance(cents INTEGER); CREATE TABLE events(id TEXT PRIMARY KEY);')
    with db:
        db.execute('INSERT INTO balance VALUES (100)')
        db.execute("INSERT INTO events VALUES ('once')")
    try:
        with db:
            db.execute('UPDATE balance SET cents=cents-20')
            db.execute("INSERT INTO events VALUES ('once')")
    except sqlite3.IntegrityError:
        pass
    print(json.dumps({'balance_cents': db.execute('SELECT cents FROM balance').fetchone()[0], 'events': db.execute('SELECT COUNT(*) FROM events').fetchone()[0]}))
