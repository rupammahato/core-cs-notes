from pathlib import Path
import os
import psycopg
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from cluster import OWNER, OWNER_PASSWORD, APP_PASSWORD

BASE=Path(__file__).resolve().parent

def connection_info(*,admin=False,name='m13-app'):
    if os.environ['M13_HOST']!='127.0.0.1': raise RuntimeError('Loopback fixture only')
    return make_conninfo(host=os.environ['M13_HOST'],port=os.environ['M13_PORT'],
                         dbname=os.environ['M13_DATABASE'],user=OWNER if admin else 'm13_app',
                         password=OWNER_PASSWORD if admin else APP_PASSWORD,
                         sslmode='disable',connect_timeout=5,application_name=name)

def connect(*,admin=False,autocommit=True,name='m13-app'):
    return psycopg.connect(connection_info(admin=admin,name=name),autocommit=autocommit)

def prepare():
    with connect(admin=True,name='m13-setup') as conn:
        conn.execute((BASE/'schema.sql').read_text(encoding='utf-8'),prepare=False)

def make_pool(*,max_size=2,min_size=1,timeout=1,reset=None,name='m13-pool'):
    pool=ConnectionPool(connection_info(name=name),min_size=min_size,max_size=max_size,
                        timeout=timeout,max_waiting=4,kwargs={'autocommit':True},
                        reset=reset,open=False)
    pool.open()
    pool.wait(timeout=5)
    return pool
