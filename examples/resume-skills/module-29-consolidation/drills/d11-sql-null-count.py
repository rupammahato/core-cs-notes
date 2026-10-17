from contextlib import closing
import json
import sqlite3

with closing(sqlite3.connect(':memory:')) as db:
    db.execute('CREATE TABLE values_table(v INTEGER)')
    db.executemany('INSERT INTO values_table VALUES (?)', [(None,), (10,), (None,)])
    row = db.execute('SELECT COUNT(*),COUNT(v),SUM(v) FROM values_table').fetchone()
    print(json.dumps({'rows': row[0], 'nonnull': row[1], 'sum': row[2]}))
