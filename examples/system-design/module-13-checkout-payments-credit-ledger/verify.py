from pathlib import Path
import hashlib
import hmac
import json
from checkout import Checkout, Provider, PROVIDER_SECRET, submit, reconcile, dispatch, estimates
from runtime import Error
from verification import Fixture

BASE = Path(__file__).resolve().parent
with Fixture('S8',BASE) as h:
    s = h.store(Checkout)
    p = h.store(Provider,'provider')
    s.product('pack',500,100)
    s.product('large',900,200)
    order = s.create('t1','alice','checkout','pack')
    h.check('checkout','server catalog snapshot',order['amount']==500 and order['credits']==100 and order['currency']=='USD')
    s.product('pack',600,120)
    h.check('checkout','replay keeps original price',s.create('t1','alice','checkout','pack')['amount']==500)
    h.denied('checkout','changed product conflicts',409,lambda:s.create('t1','alice','checkout','large'))
    h.denied('checkout','unknown product',404,lambda:s.create('t1','alice','missing','absent'))
    h.denied('authorization','owner order hidden',404,lambda:s.owned('t1','bob',order['id']))
    h.denied('authorization','tenant order hidden',404,lambda:s.owned('t2','alice',order['id']))
    lost = submit(s,p,'t1','alice',order['id'],True)
    h.check('uncertainty','timeout marks unknown',lost['state']=='unknown')
    h.check('uncertainty','provider committed before timeout',p.db.execute('SELECT count(*) FROM charges').fetchone()[0]==1)
    h.check('uncertainty','no unverified credit',s.balance('t1','alice')==0)
    charged = p.lookup(order['id'])
    recovered = submit(s,p,'t1','alice',order['id'])
    h.check('uncertainty','retry recovers same charge',recovered['state']=='paid' and p.db.execute('SELECT count(*) FROM charges').fetchone()[0]==1)
    h.check('ledger','verified success grants once',s.balance('t1','alice')==100)
    h.check('ledger','duplicate event replay',s.observe('sync_'+charged['payment_id'],order['id'],charged['payment_id'],500,'USD')=='paid')
    h.check('ledger','different event same payment dedupe',s.observe('webhook',order['id'],charged['payment_id'],500,'USD')=='paid' and s.balance('t1','alice')==100)
    h.denied('ledger','changed event conflicts',409,lambda:s.observe('webhook',order['id'],'otherpayment',500,'USD'))
    h.denied('ledger','changed payment binding conflicts',409,lambda:s.observe('changed',order['id'],charged['payment_id'],600,'USD'))
    s.unknown(order['id'])
    h.check('uncertainty','late unknown cannot downgrade paid',s.owned('t1','alice',order['id'])['state']=='paid')
    h.check('uncertainty','reconciliation idempotent',reconcile(s,p,'t1','alice',order['id'])['state']=='paid' and s.balance('t1','alice')==100)
    h.denied('uncertainty','provider key binds request',409,lambda:p.charge(order['id'],999,'USD'))
    h.observations['payment_recovery']={'injected_fault':'reply loss after provider commit','state_after_timeout':lost['state'],
        'balance_before_verification':0,'provider_charge_count_after_retry':1,'state_after_retry':recovered['state'],
        'credit_units_after_replays':100,'real_provider_network':False}
    mismatched = s.create('t1','bob','wrong','pack')
    h.check('binding','amount mismatch quarantined',s.observe('badamount',mismatched['id'],'badpay',500,'USD')=='review_required')
    h.check('binding','mismatch grants nothing',s.balance('t1','bob')==0 and s.owned('t1','bob',mismatched['id'])['review']=='amount_currency_mismatch')
    currency = s.create('t1','bob','currency','pack')
    h.check('binding','currency mismatch quarantined',s.observe('badcurrency',currency['id'],'europay',600,'EUR')=='review_required')
    h.check('binding','second charge no extra credit',s.observe('secondcharge',order['id'],'secondpay',500,'USD')=='extra_charge_review' and s.balance('t1','alice')==100)
    h.check('binding','extra charge remains visible for review',s.owned('t1','alice',order['id'])['review']=='extra_charge')
    h.denied('binding','unknown provider order',404,lambda:s.observe('absent','absent','absent',500,'USD'))
    h.denied('binding','amount boolean rejected',400,lambda:s.observe('bool',order['id'],'bool',True,'USD'))
    h.denied('binding','invalid currency rejected',400,lambda:s.observe('cur',order['id'],'cur',500,'usd'))
    h.observations['binding']={'mismatch_outcome':'review_required','mismatch_balance':0,
        'second_successful_payment_outcome':'extra_charge_review','second_credit_granted':False,
        'provider_refund_executed':False,'units_are_currency':False}
    def spend(item,key):
        try:
            return item.spend('t1','alice',key,80)
        except Error as e:
            return {'status':e.status}
    race = h.race(lambda:Checkout(h.root/'main.sqlite'),[lambda x:spend(x,'s1'),lambda x:spend(x,'s2')])
    successful = next(x for x in race if 'id' in x)
    h.check('concurrency','one of two overspending attempts wins',sum('id' in x for x in race)==1 and {'status':409} in race)
    h.check('concurrency','balance never negative',s.balance('t1','alice')==20)
    h.check('ledger','spend replay returns original journal',s.spend('t1','alice',successful['operation'],80)['id']==successful['id'])
    h.denied('ledger','changed spend intent conflicts',409,lambda:s.spend('t1','alice',successful['operation'],1))
    h.denied('ledger','zero spend rejected',400,lambda:s.spend('t1','alice','zero',0))
    h.denied('ledger','boolean spend rejected',400,lambda:s.spend('t1','alice','bool',True))
    reversal = s.reverse_spend('t1','alice','undo',successful['id'])
    h.check('ledger','reversal appends inverse',s.balance('t1','alice')==100 and reversal['kind']=='reversal')
    h.check('ledger','reversal replay stable',s.reverse_spend('t1','alice','undo',successful['id'])['id']==reversal['id'])
    h.denied('ledger','second reversal conflicts',409,lambda:s.reverse_spend('t1','alice','undo2',successful['id']))
    h.denied('authorization','other owner reversal hidden',404,lambda:s.reverse_spend('t1','bob','undo',successful['id']))
    h.check('ledger','spend replay retains historical response',s.spend('t1','alice',successful['operation'],80)['balance_after']==20 and s.balance('t1','alice')==100)
    h.check('ledger','every journal balances in one unit',s.db.execute('SELECT count(*) FROM (SELECT journal_id FROM entries GROUP BY journal_id HAVING sum(delta)!=0 OR count(*)!=2)').fetchone()[0]==0)
    h.fault('ledger','entries reject update',lambda:s.db.execute('UPDATE entries SET delta=1'),lambda:True)
    h.fault('ledger','entries reject delete',lambda:s.db.execute('DELETE FROM entries'),lambda:True)
    h.observations['concurrency']={'two_spends_of':80,'initial_credit_units':100,'successful_spends':1,
        'rejected_spends':1,'balance_after_competing_spends':20,'balance_after_appended_reversal':100,
        'historical_spend_replay_balance_after':20,'all_journal_delta_sums':0}
    atomic = s.create('t2','alice','atomic','pack')
    pay = p.charge(atomic['id'],600,'USD')
    before = s.db.execute('SELECT count(*) FROM journals').fetchone()[0]
    s.db.execute("CREATE TRIGGER stop_grant BEFORE INSERT ON grants BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','grant failure rolls back entries balance event',lambda:s.observe('atomic',atomic['id'],pay['payment_id'],600,'USD'),
        lambda:s.balance('t2','alice')==0 and s.db.execute('SELECT count(*) FROM journals').fetchone()[0]==before
        and s.db.execute("SELECT count(*) FROM events WHERE id='atomic'").fetchone()[0]==0)
    h.check('atomicity','provider remains committed despite merchant rollback',p.lookup(atomic['id']) is not None)
    s.db.execute('DROP TRIGGER stop_grant')
    outcome = h.race(lambda:Checkout(h.root/'main.sqlite'),[
        lambda x:x.observe('race_callback',atomic['id'],pay['payment_id'],600,'USD'),
        lambda x:x.observe('race_reconcile',atomic['id'],pay['payment_id'],600,'USD')])
    h.check('concurrency','callback and reconciliation converge',outcome==['paid','paid'] and s.balance('t2','alice')==120)
    before = s.db.execute('SELECT count(*) FROM journals').fetchone()[0]
    s.db.execute("CREATE TRIGGER stop_entry BEFORE INSERT ON entries WHEN NEW.number=2 BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','second entry fault rolls back spend',lambda:s.spend('t2','alice','fault',30),
        lambda:s.balance('t2','alice')==120 and s.db.execute('SELECT count(*) FROM journals').fetchone()[0]==before)
    s.db.execute('DROP TRIGGER stop_entry')
    h.check('atomicity','retry after entry fault succeeds',s.spend('t2','alice','fault',30)['balance_after']==90)
    s.close()
    s = h.store(Checkout)
    h.check('atomicity','ledger survives reopen',s.balance('t2','alice')==90)
    h.observations['rollback_reconciliation']={'provider_commit_survived_merchant_fault':True,
        'merchant_grant_transaction_rolled_back':True,'callback_reconciliation_outcomes':outcome,
        'single_recovered_grant_units':120,'second_entry_rollback_tested':True,'actual_process_kill':False}
    controls = {'lose_next_reply':True}
    def http(item,user,method,path,raw,headers):
        return dispatch(item,user,method,path,raw,headers,lambda:Provider(h.root/'provider.sqlite'),controls)
    port = h.serve(lambda:Checkout(h.root/'main.sqlite'),http)
    response = h.request(port,'POST','/orders',{'sku':'pack'},headers={'Idempotency-Key':'http'})
    oid = response[2]['id']
    h.check('http','create from catalog',response[0]==201 and response[2]['amount']==600)
    h.check('http','client price cannot be supplied',h.request(port,'POST','/orders',{'sku':'pack','amount':1},headers={'Idempotency-Key':'price'})[0]==400)
    h.check('http','timeout returns accepted unknown',h.request(port,'POST','/orders/'+oid+'/submit')[0]==202)
    charged = p.lookup(oid)
    value = {'event_id':'http_callback','order_id':oid,'payment_id':charged['payment_id'],'amount':600,'currency':'USD'}
    raw = json.dumps(value,separators=(',',':')).encode()
    signature = hmac.new(PROVIDER_SECRET,raw,hashlib.sha256).hexdigest()
    h.check('http','unsigned callback rejected',h.request(port,'POST','/provider/succeeded',raw,token=None)[0]==401)
    h.check('http','signed raw callback accepted',h.request(port,'POST','/provider/succeeded',raw,token=None,headers={'X-Lesson-Signature':signature})[2]['outcome']=='paid')
    h.check('http','body tampering rejected',h.request(port,'POST','/provider/succeeded',raw+b' ',token=None,headers={'X-Lesson-Signature':signature})[0]==401)
    h.check('http','paid submit replay succeeds',h.request(port,'POST','/orders/'+oid+'/submit')[0]==200)
    h.check('http','foreign order hidden',h.request(port,'GET','/orders/'+oid,token='lesson-bob')[0]==404)
    h.check('http','foreign tenant hidden',h.request(port,'GET','/orders/'+oid,token='lesson-other')[0]==404)
    h.check('http','anonymous balance denied',h.request(port,'GET','/balance',token=None)[0]==401)
    h.check('http','balance reads integer units',h.request(port,'GET','/balance')[2]=={'units':220,'unit':'CREDIT'})
    h.check('http','spend endpoint',h.request(port,'POST','/spends',{'units':5},headers={'Idempotency-Key':'http_spend'})[0]==201)
    h.observations['http_contract']={'create_order':201,'provider_timeout_submit':202,'verified_callback':200,
        'tampered_callback':401,'paid_submit_replay':200,'other_owner':404,'other_tenant':404,
        'anonymous_balance':401,'real_merchant_loopback_HTTP':True,'provider_is_local_separate_SQLite':True}
    h.observations['estimates'] = estimates()
h.report('Separate local provider and merchant SQLite stores; injected reply loss after provider commit, immutable catalog snapshots, signed fixture callback, payment/event/grant dedupe, balanced integer credit journals, competing spends, reversal, rollback and real merchant loopback HTTP. No real charge, bank ledger, card data, refund or provider network.')
