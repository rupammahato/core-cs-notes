"""Use only the workspace's matching portable PostgreSQL/pgvector runtime."""
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import psycopg
from psycopg import sql

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('placement_m13_cluster', BASE / 'cluster_runtime.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


@contextmanager
def temporary_cluster():
    original_path = os.environ.get('PATH', '')
    os.environ['PATH'] = str(BASE / '.runtime/Library/bin') + os.pathsep + original_path
    try:
        with previous.temporary_cluster() as (params, evidence):
            with psycopg.connect(**params, autocommit=True) as admin:
                admin.execute((BASE / 'schema.sql').read_text(encoding='utf-8'))
                evidence['pgvector'] = admin.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()[0]
            yield params, evidence
    finally:
        os.environ['PATH'] = original_path
