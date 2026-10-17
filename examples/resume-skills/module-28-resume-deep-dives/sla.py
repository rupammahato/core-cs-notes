"""Illustrative business-date SLA state and transactional alert-outbox model."""
from datetime import date, timedelta


def business_due(start, days, holidays=frozenset()):
    if type(start) is not date or type(days) is not int or days < 0:
        raise ValueError('Expected business date and nonnegative day count')
    current = start
    remaining = days
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            remaining -= 1
    return current


def initialize(db):
    db.executescript('''
        CREATE TABLE tasks (
            tenant TEXT NOT NULL, id TEXT NOT NULL, due TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('open','in_progress','done')),
            version INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(tenant,id)
        );
        CREATE TABLE audit (
            tenant TEXT NOT NULL, task TEXT NOT NULL, old_state TEXT NOT NULL,
            new_state TEXT NOT NULL, version INTEGER NOT NULL,
            UNIQUE(tenant,task,version)
        );
        CREATE TABLE alerts (
            tenant TEXT NOT NULL, task TEXT NOT NULL, tier INTEGER NOT NULL,
            business_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            PRIMARY KEY(tenant,task,tier)
        );
    ''')


def transition(db, tenant, task_id, expected_version, target):
    allowed = {'open': {'in_progress'}, 'in_progress': {'done'}, 'done': set()}
    with db:
        row = db.execute('SELECT state,version FROM tasks WHERE tenant=? AND id=?', (tenant, task_id)).fetchone()
        if not row:
            raise LookupError('Task absent in tenant')
        state, version = row
        if version != expected_version:
            raise ValueError('Stale version')
        if target not in allowed[state]:
            raise ValueError('Invalid state transition')
        changed = db.execute('UPDATE tasks SET state=?,version=version+1 WHERE tenant=? AND id=? AND version=?', (target, tenant, task_id, expected_version)).rowcount
        if changed != 1:
            raise ValueError('Concurrent state change')
        db.execute('INSERT INTO audit VALUES (?,?,?,?,?)', (tenant, task_id, state, target, version + 1))


def scan(db, business_date):
    if type(business_date) is not date:
        raise ValueError('Caller must supply the calendar-local business date')
    created = 0
    with db:
        for tenant, task_id, due_text in db.execute("SELECT tenant,id,due FROM tasks WHERE state!='done'").fetchall():
            late_days = (business_date - date.fromisoformat(due_text)).days
            # Tiers use elapsed calendar days after the working-day due date in this toy policy.
            tier = 2 if late_days >= 3 else 1 if late_days >= 1 else 0
            if tier:
                created += db.execute('INSERT OR IGNORE INTO alerts(tenant,task,tier,business_date) VALUES (?,?,?,?)', (tenant, task_id, tier, business_date.isoformat())).rowcount
    return created
