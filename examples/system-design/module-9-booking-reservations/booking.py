"""Assigned-seat holds and trusted payment observations; no real payment calls."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
import hashlib
import hmac
import json
import re
import uuid
from runtime import Database, Error, document, identity, number, require

LESSON_PROVIDER_SECRET = b'published-s4-provider-secret'


class Booking(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS seats(tenant TEXT,show TEXT,id TEXT,price INTEGER NOT NULL,
            hold_id TEXT,PRIMARY KEY(tenant,show,id));
        CREATE TABLE IF NOT EXISTS holds(id TEXT PRIMARY KEY,tenant TEXT,owner TEXT,operation TEXT,
            show TEXT,seats TEXT,amount INTEGER,currency TEXT,expires INTEGER,state TEXT,
            UNIQUE(tenant,owner,operation));
        CREATE INDEX IF NOT EXISTS hold_expiry ON holds(state,expires);
        CREATE TABLE IF NOT EXISTS payments(id TEXT PRIMARY KEY,fingerprint TEXT,outcome TEXT);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,fingerprint TEXT,outcome TEXT);
        CREATE TABLE IF NOT EXISTS refunds(payment_id TEXT PRIMARY KEY,state TEXT);
    '''

    def seed(self, tenant, show, seats):
        # Trusted fixture/admin operation; no public inventory-edit endpoint.
        with self.transaction():
            for seat, price in seats.items():
                self.db.execute('INSERT INTO seats VALUES(?,?,?,?,NULL)',(identity(tenant),identity(show),identity(seat),number(price,1,1000000)))

    def expire(self, now):
        self.db.execute("UPDATE holds SET state='expired' WHERE state='held' AND expires<=?",(now,))
        self.db.execute("UPDATE seats SET hold_id=NULL WHERE hold_id IN (SELECT id FROM holds WHERE state IN ('expired','cancelled'))")

    def owned(self, tenant, owner, hold_id):
        row = self.db.execute('SELECT * FROM holds WHERE tenant=? AND owner=? AND id=?',
                              (identity(tenant),identity(owner),identity(hold_id))).fetchone()
        if row is None:
            raise Error(404,'hold_not_found')
        return dict(row)

    def reserve(self, tenant, owner, operation, show, seats, now):
        for value in (tenant,owner,operation,show):
            identity(value)
        number(now)
        if type(seats) is not list or not 1 <= len(seats) <= 4:
            raise Error(400,'one_to_four_seats')
        for seat in seats:
            identity(seat)
        if len(set(seats)) != len(seats):
            raise Error(400,'duplicate_seat')
        selected = json.dumps(sorted(seats),separators=(',',':'))
        with self.transaction():
            self.expire(now)
            old = self.db.execute('SELECT * FROM holds WHERE tenant=? AND owner=? AND operation=?',
                                  (tenant,owner,operation)).fetchone()
            if old:
                if (old['show'],old['seats']) != (show,selected):
                    raise Error(409,'changed_reservation_intent')
                return dict(old)
            if self.db.execute('SELECT count(*) FROM holds').fetchone()[0]>=128:
                raise Error(503,'lesson_hold_retention_cap')
            rows = [self.db.execute('SELECT * FROM seats WHERE tenant=? AND show=? AND id=?',(tenant,show,seat)).fetchone() for seat in sorted(seats)]
            if any(row is None for row in rows):
                raise Error(404,'seat_not_found')
            if any(row['hold_id'] is not None for row in rows):
                raise Error(409,'seat_unavailable')
            hold_id = uuid.uuid4().hex
            self.db.execute('INSERT INTO holds VALUES(?,?,?,?,?,?,?,?,?,?)',
                (hold_id,tenant,owner,operation,show,selected,sum(row['price'] for row in rows),'USD',now+5000,'held'))
            for seat in sorted(seats):
                changed = self.db.execute('UPDATE seats SET hold_id=? WHERE tenant=? AND show=? AND id=? AND hold_id IS NULL',
                                          (hold_id,tenant,show,seat)).rowcount
                if changed != 1:
                    raise Error(409,'seat_unavailable')
            return self.owned(tenant,owner,hold_id)

    def status(self, tenant, owner, hold_id, now):
        number(now)
        with self.transaction():
            self.expire(now)
            return self.owned(tenant,owner,hold_id)

    def cancel(self, tenant, owner, hold_id, now):
        number(now)
        with self.transaction():
            self.expire(now)
            row = self.owned(tenant,owner,hold_id)
            if row['state'] == 'confirmed':
                raise Error(409,'confirmed_cancellation_not_implemented')
            if row['state'] == 'held':
                self.db.execute("UPDATE holds SET state='cancelled' WHERE id=?",(hold_id,))
                self.db.execute('UPDATE seats SET hold_id=NULL WHERE hold_id=?',(hold_id,))
            return self.owned(tenant,owner,hold_id)

    def payment(self, tenant, event_id, payment_id, hold_id, amount, currency, now):
        # Called only after authenticating the provider observation, never a browser claim.
        for value in (tenant,event_id,payment_id,hold_id):
            identity(value)
        number(amount,1,10000000)
        number(now)
        if type(currency) is not str or not re.fullmatch(r'[A-Z]{3}',currency):
            raise Error(400,'invalid_currency')
        fingerprint = json.dumps([tenant,payment_id,hold_id,amount,currency],separators=(',',':'))
        with self.transaction():
            prior = self.db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if prior:
                if prior['fingerprint'] != fingerprint:
                    raise Error(409,'changed_event')
                return prior['outcome']
            paid = self.db.execute('SELECT * FROM payments WHERE id=?',(payment_id,)).fetchone()
            if paid:
                if paid['fingerprint'] != fingerprint:
                    raise Error(409,'changed_payment_binding')
                outcome = paid['outcome']
            else:
                self.expire(now)
                hold = self.db.execute('SELECT * FROM holds WHERE tenant=? AND id=?',(tenant,hold_id)).fetchone()
                if hold is None:
                    raise Error(404,'payment_hold_not_found')
                if (hold['amount'],hold['currency']) != (amount,currency):
                    outcome = 'review_required'
                elif hold['state'] == 'held' and hold['expires']>now:
                    owned = self.db.execute('SELECT count(*) FROM seats WHERE hold_id=?',(hold_id,)).fetchone()[0]
                    if owned != len(json.loads(hold['seats'])):
                        raise Error(409,'inventory_invariant_broken')
                    self.db.execute("UPDATE holds SET state='confirmed' WHERE id=?",(hold_id,))
                    outcome = 'confirmed'
                else:
                    outcome = 'refund_required'
                    self.db.execute("INSERT INTO refunds VALUES(?,'pending')",(payment_id,))
                self.db.execute('INSERT INTO payments VALUES(?,?,?)',(payment_id,fingerprint,outcome))
            self.db.execute('INSERT INTO events VALUES(?,?,?)',(event_id,fingerprint,outcome))
            return outcome


def estimates():
    return {'contenders_per_minute':10000,'average_reservation_attempts_per_second':round(10000/60,3),
        'assumed_logical_hold_bytes':512,'one_million_retained_holds_MB':512,
        'hold_window_ms_in_fixture':5000,'seats_per_reservation_max':4,'measured_capacity':False}


def dispatch(item, user, method, path, raw, headers, now):
    if path == '/provider/payment-success' and method == 'POST':
        expected = hmac.new(LESSON_PROVIDER_SECRET,raw,hashlib.sha256).hexdigest()
        supplied = headers.get('X-Lesson-Signature','')
        if not supplied.isascii() or not hmac.compare_digest(expected,supplied):
            raise Error(401,'invalid_provider_signature')
        value = document(raw,['tenant','event_id','payment_id','hold_id','amount','currency'])
        return 200,{'outcome':item.payment(**value,now=now)}
    tenant, owner = require(user)
    if path == '/holds' and method == 'POST':
        value = document(raw,['show','seats'])
        return 201,item.reserve(tenant,owner,headers.get('Idempotency-Key',''),value['show'],value['seats'],now)
    match = re.fullmatch(r'/holds/([a-f0-9]{32})',path)
    if match and method == 'GET':
        return 200,item.status(tenant,owner,match[1],now)
    if match and method == 'DELETE':
        return 200,item.cancel(tenant,owner,match[1],now)
    raise Error(404,'unknown_route')
