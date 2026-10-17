"""Closed-unit credit ledger plus separate local provider store; no real money."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
import hashlib
import hmac
import json
import re
import uuid
from runtime import Database, Error, document, identity, number, require

PROVIDER_SECRET = b'published-s8-provider-fixture-secret'


class Provider(Database):
    schema = '''CREATE TABLE IF NOT EXISTS charges(request_id TEXT PRIMARY KEY,payment_id TEXT UNIQUE,
        amount INTEGER,currency TEXT,status TEXT);'''

    def charge(self,request_id,amount,currency,lose_reply=False):
        with self.transaction():
            old = self.db.execute('SELECT * FROM charges WHERE request_id=?',(request_id,)).fetchone()
            if old and (old['amount'],old['currency']) != (amount,currency):
                raise Error(409,'provider_idempotency_conflict')
            if old is None:
                self.db.execute("INSERT INTO charges VALUES(?,?,?,?,'succeeded')",(request_id,uuid.uuid4().hex,amount,currency))
            result = dict(self.db.execute('SELECT * FROM charges WHERE request_id=?',(request_id,)).fetchone())
        if lose_reply:
            raise TimeoutError('injected reply loss AFTER provider commit')
        return result

    def lookup(self,request_id):
        row = self.db.execute('SELECT * FROM charges WHERE request_id=?',(request_id,)).fetchone()
        return dict(row) if row else None


class Checkout(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS catalog(sku TEXT PRIMARY KEY,amount INTEGER,currency TEXT,credits INTEGER);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,tenant TEXT,owner TEXT,operation TEXT,
            sku TEXT,amount INTEGER,currency TEXT,credits INTEGER,state TEXT,review TEXT,
            UNIQUE(tenant,owner,operation));
        CREATE TABLE IF NOT EXISTS observations(payment_id TEXT PRIMARY KEY,fingerprint TEXT,outcome TEXT);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,fingerprint TEXT,outcome TEXT);
        CREATE TABLE IF NOT EXISTS grants(order_id TEXT PRIMARY KEY,payment_id TEXT UNIQUE,journal_id TEXT);
        CREATE TABLE IF NOT EXISTS balances(tenant TEXT,owner TEXT,units INTEGER CHECK(units>=0),PRIMARY KEY(tenant,owner));
        CREATE TABLE IF NOT EXISTS journals(id TEXT PRIMARY KEY,tenant TEXT,owner TEXT,operation TEXT,
            kind TEXT,units INTEGER,reference TEXT,balance_after INTEGER,UNIQUE(tenant,owner,kind,operation));
        CREATE TABLE IF NOT EXISTS entries(journal_id TEXT,number INTEGER,tenant TEXT,account TEXT,
            delta INTEGER,unit TEXT,PRIMARY KEY(journal_id,number));
        CREATE TABLE IF NOT EXISTS reversals(original TEXT PRIMARY KEY,reversal TEXT UNIQUE);
        CREATE TRIGGER IF NOT EXISTS immutable_entry_update BEFORE UPDATE ON entries BEGIN SELECT RAISE(ABORT,'append_only'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_entry_delete BEFORE DELETE ON entries BEGIN SELECT RAISE(ABORT,'append_only'); END;
    '''

    def product(self,sku,amount,credits):
        # Trusted catalog fixture, not a public endpoint or currency conversion engine.
        self.db.execute("INSERT INTO catalog VALUES(?,?,'USD',?) ON CONFLICT(sku) DO UPDATE SET amount=excluded.amount,credits=excluded.credits",
                        (identity(sku),number(amount,1,1000000),number(credits,1,1000000)))

    def owned(self,tenant,owner,order_id):
        row = self.db.execute('SELECT * FROM orders WHERE tenant=? AND owner=? AND id=?',(identity(tenant),identity(owner),identity(order_id))).fetchone()
        if row is None:
            raise Error(404,'order_not_found')
        return dict(row)

    def create(self,tenant,owner,operation,sku):
        for value in (tenant,owner,operation,sku):
            identity(value)
        with self.transaction():
            old = self.db.execute('SELECT * FROM orders WHERE tenant=? AND owner=? AND operation=?',(tenant,owner,operation)).fetchone()
            if old:
                if old['sku'] != sku:
                    raise Error(409,'changed_checkout_intent')
                return dict(old)
            item = self.db.execute('SELECT * FROM catalog WHERE sku=?',(sku,)).fetchone()
            if item is None:
                raise Error(404,'product_not_found')
            if self.db.execute('SELECT count(*) FROM orders').fetchone()[0]>=128:
                raise Error(503,'lesson_order_retention_cap')
            order_id = uuid.uuid4().hex
            self.db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,'pending',NULL)",
                (order_id,tenant,owner,operation,sku,item['amount'],item['currency'],item['credits']))
            return self.owned(tenant,owner,order_id)

    def unknown(self,order_id):
        self.db.execute("UPDATE orders SET state='unknown' WHERE id=? AND state='pending'",(order_id,))

    def balance(self,tenant,owner):
        row = self.db.execute('SELECT units FROM balances WHERE tenant=? AND owner=?',(identity(tenant),identity(owner))).fetchone()
        return row[0] if row else 0

    def _post(self,tenant,owner,operation,kind,units,reference):
        old = self.db.execute('SELECT * FROM journals WHERE tenant=? AND owner=? AND kind=? AND operation=?',(tenant,owner,kind,operation)).fetchone()
        if old:
            if (old['units'],old['reference']) != (units,reference):
                raise Error(409,'changed_ledger_intent')
            return dict(old)
        if self.db.execute('SELECT count(*) FROM journals').fetchone()[0]>=256:
            raise Error(503,'lesson_journal_retention_cap')
        self.db.execute('INSERT INTO balances VALUES(?,?,0) ON CONFLICT DO NOTHING',(tenant,owner))
        delta = -units if kind=='spend' else units
        changed = self.db.execute('UPDATE balances SET units=units+? WHERE tenant=? AND owner=? AND units+?>=0',
                                  (delta,tenant,owner,delta)).rowcount
        if changed!=1:
            raise Error(409,'insufficient_credits')
        journal_id = uuid.uuid4().hex
        after = self.balance(tenant,owner)
        self.db.execute('INSERT INTO journals VALUES(?,?,?,?,?,?,?,?)',(journal_id,tenant,owner,operation,kind,units,reference,after))
        counterpart = 'consumption' if kind=='spend' else 'issuance' if kind=='grant' else 'consumption'
        self.db.execute("INSERT INTO entries VALUES(?,1,?,?,?,'CREDIT')",(journal_id,tenant,'user:'+owner,delta))
        self.db.execute("INSERT INTO entries VALUES(?,2,?,?,?,'CREDIT')",(journal_id,tenant,counterpart,-delta))
        return dict(self.db.execute('SELECT * FROM journals WHERE id=?',(journal_id,)).fetchone())

    def observe(self,event_id,order_id,payment_id,amount,currency):
        for value in (event_id,order_id,payment_id):
            identity(value)
        number(amount,1,10000000)
        if type(currency) is not str or not re.fullmatch(r'[A-Z]{3}',currency):
            raise Error(400,'invalid_currency')
        fingerprint = json.dumps([order_id,payment_id,amount,currency],separators=(',',':'))
        with self.transaction():
            event = self.db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if event:
                if event['fingerprint'] != fingerprint:
                    raise Error(409,'changed_provider_event')
                return event['outcome']
            prior = self.db.execute('SELECT * FROM observations WHERE payment_id=?',(payment_id,)).fetchone()
            if prior:
                if prior['fingerprint'] != fingerprint:
                    raise Error(409,'changed_payment_binding')
                outcome = prior['outcome']
            else:
                order = self.db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
                if order is None:
                    raise Error(404,'provider_order_not_found')
                if (amount,currency)!=(order['amount'],order['currency']):
                    outcome = 'review_required'
                    self.db.execute("UPDATE orders SET review='amount_currency_mismatch' WHERE id=?",(order_id,))
                elif self.db.execute('SELECT 1 FROM grants WHERE order_id=?',(order_id,)).fetchone():
                    outcome = 'extra_charge_review'
                    self.db.execute("UPDATE orders SET review='extra_charge' WHERE id=?",(order_id,))
                else:
                    journal = self._post(order['tenant'],order['owner'],order_id,'grant',order['credits'],order_id)
                    self.db.execute('INSERT INTO grants VALUES(?,?,?)',(order_id,payment_id,journal['id']))
                    self.db.execute("UPDATE orders SET state='paid',review=NULL WHERE id=?",(order_id,))
                    outcome = 'paid'
                self.db.execute('INSERT INTO observations VALUES(?,?,?)',(payment_id,fingerprint,outcome))
            self.db.execute('INSERT INTO events VALUES(?,?,?)',(event_id,fingerprint,outcome))
            return outcome

    def spend(self,tenant,owner,operation,units):
        for value in (tenant,owner,operation):
            identity(value)
        number(units,1,1000000)
        with self.transaction():
            return self._post(tenant,owner,operation,'spend',units,'')

    def reverse_spend(self,tenant,owner,operation,journal_id):
        for value in (tenant,owner,operation,journal_id):
            identity(value)
        with self.transaction():
            original = self.db.execute("SELECT * FROM journals WHERE id=? AND tenant=? AND owner=? AND kind='spend'",(journal_id,tenant,owner)).fetchone()
            if original is None:
                raise Error(404,'spend_not_found')
            old = self.db.execute("SELECT * FROM journals WHERE tenant=? AND owner=? AND kind='reversal' AND operation=?",(tenant,owner,operation)).fetchone()
            if old:
                if old['reference']!=journal_id:
                    raise Error(409,'changed_reversal_intent')
                return dict(old)
            if self.db.execute('SELECT 1 FROM reversals WHERE original=?',(journal_id,)).fetchone():
                raise Error(409,'already_reversed')
            result = self._post(tenant,owner,operation,'reversal',original['units'],journal_id)
            self.db.execute('INSERT INTO reversals VALUES(?,?)',(journal_id,result['id']))
            return result


def submit(item,provider,tenant,owner,order_id,lose_reply=False):
    order = item.owned(tenant,owner,order_id)
    if order['state']=='paid':
        return order
    try:
        charged = provider.charge(order_id,order['amount'],order['currency'],lose_reply)
    except TimeoutError:
        item.unknown(order_id)
    else:
        item.observe('sync_'+charged['payment_id'],order_id,charged['payment_id'],charged['amount'],charged['currency'])
    return item.owned(tenant,owner,order_id)


def reconcile(item,provider,tenant,owner,order_id):
    item.owned(tenant,owner,order_id)
    charged = provider.lookup(order_id)
    if charged:
        item.observe('reconcile_'+charged['payment_id'],order_id,charged['payment_id'],charged['amount'],charged['currency'])
    return item.owned(tenant,owner,order_id)


def estimates():
    return {'successful_topups_per_day':100000,'entries_per_grant':2,'daily_grant_entries':200000,
        'assumed_entry_bytes':192,'thirty_day_logical_entry_GB':1.152,'credit_unit':'integer CREDIT',
        'fixture_USD_product_minor_units':500,'fixture_product_credit_units':100,'measured_capacity':False}


def dispatch(item,user,method,path,raw,headers,provider_factory,controls):
    if method=='POST' and path=='/provider/succeeded':
        supplied = headers.get('X-Lesson-Signature','')
        expected = hmac.new(PROVIDER_SECRET,raw,hashlib.sha256).hexdigest()
        if not supplied.isascii() or not hmac.compare_digest(expected,supplied):
            raise Error(401,'invalid_provider_signature')
        value = document(raw,['event_id','order_id','payment_id','amount','currency'])
        return 200,{'outcome':item.observe(**value)}
    tenant,owner = require(user)
    if method=='POST' and path=='/orders':
        value = document(raw,['sku'])
        return 201,item.create(tenant,owner,headers.get('Idempotency-Key',''),value['sku'])
    match = re.fullmatch(r'/orders/([a-f0-9]{32})(/submit)?',path)
    if match and method=='GET' and not match[2]:
        return 200,item.owned(tenant,owner,match[1])
    if match and method=='POST' and match[2]:
        provider = provider_factory()
        try:
            lose = controls.pop('lose_next_reply',False)
            order = submit(item,provider,tenant,owner,match[1],lose)
            return (200 if order['state']=='paid' else 202),order
        finally:
            provider.close()
    if path=='/balance' and method=='GET':
        return 200,{'units':item.balance(tenant,owner),'unit':'CREDIT'}
    if path=='/spends' and method=='POST':
        value = document(raw,['units'])
        return 201,item.spend(tenant,owner,headers.get('Idempotency-Key',''),value['units'])
    raise Error(404,'unknown_route')
