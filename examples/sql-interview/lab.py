"""In-memory SQLite runner for the synthetic SQL interview lab."""
from pathlib import Path
import json
import sqlite3
import sys

BASE=Path(__file__).resolve().parent

def load_fixture():
    return json.loads((BASE/'fixture.json').read_text(encoding='utf-8'))

def parameters():
    return json.loads((BASE/'parameters.json').read_text(encoding='utf-8'))

def connect(fixture=None,reverse=False):
    fixture=fixture or load_fixture()
    db=sqlite3.connect(':memory:')
    db.row_factory=sqlite3.Row
    try:
        db.executescript((BASE/'schema.sql').read_text(encoding='utf-8'))
        for table,rows in fixture['tables'].items():
            if rows:
                placeholders=','.join('?' for _ in rows[0])
                db.executemany(f'INSERT INTO {table} VALUES ({placeholders})',list(reversed(rows)) if reverse else rows)
        db.commit()
        return db
    except BaseException:
        db.close()
        raise

def query(db,number,params=None):
    source=(BASE/'queries'/f'q{number:02}.sql').read_text(encoding='utf-8')
    return [dict(row) for row in db.execute(source,params or parameters())]

if __name__=='__main__':
    number=int(sys.argv[1].upper().removeprefix('Q')) if len(sys.argv)>1 else 1
    if not 1<=number<=30:raise SystemExit('Choose Q01 through Q30')
    db=connect()
    try:print(json.dumps(query(db,number),indent=2))
    finally:db.close()
