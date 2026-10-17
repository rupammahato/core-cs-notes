from contextlib import contextmanager
from pathlib import Path
import sqlite3

SCHEMA='''
CREATE TABLE jobs(
 id TEXT PRIMARY KEY,tenant_id INTEGER NOT NULL CHECK(tenant_id>0),
 operation_key TEXT NOT NULL,payload TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('ready','running','done','failed')),
 attempts INTEGER NOT NULL DEFAULT 0,available_at REAL NOT NULL,
 lease_until REAL,token TEXT,last_error TEXT,
 UNIQUE(tenant_id,operation_key));
CREATE TABLE effects(tenant_id INTEGER NOT NULL,operation_key TEXT NOT NULL,
 amount INTEGER NOT NULL CHECK(amount>0),PRIMARY KEY(tenant_id,operation_key));
CREATE TABLE imports(tenant_id INTEGER NOT NULL,import_key TEXT NOT NULL,digest TEXT NOT NULL,
 checkpoint INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL DEFAULT 'running',
 PRIMARY KEY(tenant_id,import_key));
CREATE TABLE records(tenant_id INTEGER NOT NULL,external_id TEXT NOT NULL,
 name TEXT NOT NULL,amount_minor INTEGER NOT NULL CHECK(amount_minor>=0),
 source_version INTEGER NOT NULL CHECK(source_version>=0),source_time TEXT NOT NULL,
 PRIMARY KEY(tenant_id,external_id));
'''

@contextmanager
def connect(filename):
    conn=sqlite3.connect(filename,isolation_level=None,timeout=3)
    conn.row_factory=sqlite3.Row
    try:yield conn
    finally:conn.close()

def prepare(filename):
    with connect(filename) as conn:conn.executescript(SCHEMA)

@contextmanager
def transaction(conn):
    if conn.in_transaction:raise ValueError('transaction owner requires idle connection')
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
        conn.execute('COMMIT')
    except BaseException:
        conn.execute('ROLLBACK')
        raise
