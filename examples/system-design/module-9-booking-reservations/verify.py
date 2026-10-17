from booking import Booking, Error, LESSON_PROVIDER_SECRET, dispatch, estimates
from verification import Fixture
from pathlib import Path
import hashlib
import hmac
import json

BASE = Path(__file__).resolve().parent
with Fixture('S4',BASE) as h:
    s = h.store(Booking)
    s.seed('t1','show',{'A':1000,'B':1500,'C':2000,'D':2500})
    for name,seats in [('empty',[]),('duplicate',['A','A']),('too_many',['A','B','C','D','E']),('invalid_identity',['../A'])]:
        h.denied('validation',name,400,lambda seats=seats:s.reserve('t1','alice','invalid','show',seats,0))
    h.denied('validation','negative server time',400,lambda:s.reserve('t1','alice','time','show',['A'],-1))
    h.denied('validation','boolean time',400,lambda:s.reserve('t1','alice','time','show',['A'],True))
    h.denied('validation','missing seat',404,lambda:s.reserve('t1','alice','missing','show',['Z'],0))
    first = s.reserve('t1','alice','op','show',['B','A'],0)
    replay = s.reserve('t1','alice','op','show',['A','B'],100)
    h.check('holds','canonical seat order replays original hold',replay['id'] == first['id'])
    h.check('holds','server sums integer minor units',first['amount'] == 2500 and first['currency'] == 'USD')
    h.check('holds','retry does not renew deadline',replay['expires'] == 5000)
    h.denied('holds','changed operation conflicts',409,lambda:s.reserve('t1','alice','op','show',['C'],100))
    h.denied('holds','another owner cannot inspect',404,lambda:s.status('t1','bob',first['id'],100))
    h.denied('holds','another tenant cannot cancel',404,lambda:s.cancel('t2','alice',first['id'],100))
    h.denied('holds','unavailable member makes group fail atomically',409,lambda:s.reserve('t1','bob','group','show',['B','C'],100))
    h.check('holds','failed group leaves other seat free',s.db.execute("SELECT hold_id FROM seats WHERE id='C'").fetchone()[0] is None)
    h.check('holds','hold valid immediately before deadline',s.status('t1','alice',first['id'],4999)['state'] == 'held')
    h.check('holds','deadline equality means expired',s.status('t1','alice',first['id'],5000)['state'] == 'expired')
    newer = s.reserve('t1','bob','new','show',['A'],5000)
    s.cancel('t1','alice',first['id'],5001)
    h.check('holds','old cancel cannot release newly held seat',s.db.execute("SELECT hold_id FROM seats WHERE id='A'").fetchone()[0] == newer['id'])
    h.check('holds','expired create replay does not reacquire',s.reserve('t1','alice','op','show',['A','B'],5001)['state'] == 'expired')
    cancelled = s.reserve('t1','alice','cancel','show',['D'],5001)
    h.check('holds','cancel held seat releases it',s.cancel('t1','alice',cancelled['id'],5002)['state'] == 'cancelled')
    h.check('holds','repeat cancel remains terminal',s.cancel('t1','alice',cancelled['id'],5003)['state'] == 'cancelled')
    rollback = h.store(Booking,'rollback')
    rollback.seed('t1','show',{'A':1000,'B':1000})
    rollback.db.execute("CREATE TRIGGER fail_second BEFORE UPDATE ON seats WHEN NEW.id='B' BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('holds','partial group writes roll back',lambda:rollback.reserve('t1','alice','op','show',['A','B'],0),
        lambda:rollback.db.execute('SELECT count(*) FROM holds').fetchone()[0] == 0 and all(row[0] is None for row in rollback.db.execute('SELECT hold_id FROM seats')))
    h.observations['holds'] = {'group_amount_minor_units':2500,'currency':'USD','hold_deadline_ms':5000,
        'expiry_at_equality':True,'replay_renews_deadline':False,'failed_group_partially_reserves':False,
        'old_cancellation_releases_new_owner':False,'partial_update_rollback_tested':True}

    race = h.store(Booking,'race')
    race.seed('t1','show',{'LAST':1000})
    def attempt(item,owner):
        try:
            return item.reserve('t1',owner,'op','show',['LAST'],0)
        except Error as error:
            return error.status
    results = h.race(lambda:Booking(h.root/'race.sqlite'),[lambda item:attempt(item,'alice'),lambda item:attempt(item,'bob')])
    winners = [value for value in results if type(value) is dict]
    h.check('concurrency','two independent callers get one last-seat hold',len(winners)==1 and 409 in results)
    winner = winners[0]
    next_owner = 'bob' if winner['owner']=='alice' else 'alice'
    replacement = race.reserve('t1',next_owner,'replacement','show',['LAST'],5000)
    late = race.payment('t1','late-event','late-payment',winner['id'],1000,'USD',5000)
    h.check('payments','late payment creates refund intent',late == 'refund_required')
    h.check('payments','late payment cannot steal reallocated inventory',race.db.execute('SELECT hold_id FROM seats').fetchone()[0] == replacement['id'])
    h.check('payments','repeat event replays durable compensation outcome',race.payment('t1','late-event','late-payment',winner['id'],1000,'USD',5001) == late)
    h.check('payments','different event same payment does not duplicate refund',race.payment('t1','late-event-2','late-payment',winner['id'],1000,'USD',5001) == late and race.db.execute('SELECT count(*) FROM refunds').fetchone()[0] == 1)
    h.denied('payments','changed event binding conflicts',409,lambda:race.payment('t1','late-event','other-payment',winner['id'],1000,'USD',5001))
    h.denied('payments','changed payment amount conflicts across event IDs',409,lambda:race.payment('t1','late-event-3','late-payment',winner['id'],999,'USD',5001))
    h.check('payments','current owner can confirm before expiry',race.payment('t1','new-event','new-payment',replacement['id'],1000,'USD',9999) == 'confirmed')
    h.check('payments','confirmed seat survives later expiry sweep',race.status('t1',next_owner,replacement['id'],10000)['state'] == 'confirmed')
    h.denied('payments','confirmed cancellation is explicit unsupported policy',409,lambda:race.cancel('t1',next_owner,replacement['id'],10000))
    h.check('payments','second charge after confirmation needs compensation',race.payment('t1','extra-event','extra-payment',replacement['id'],1000,'USD',10000) == 'refund_required')
    amount_hold = s.reserve('t1','alice','amount','show',['C'],5004)
    h.check('payments','amount mismatch does not confirm inventory',s.payment('t1','wrong-amount','underpaid',amount_hold['id'],1,'USD',5005) == 'review_required' and s.status('t1','alice',amount_hold['id'],5005)['state'] == 'held')
    h.check('payments','currency mismatch is held for review',s.payment('t1','wrong-currency','currency-payment',amount_hold['id'],2000,'EUR',5005) == 'review_required')
    race.close()
    reopened = h.store(Booking,'race')
    h.check('payments','close/reopen preserves payment outcome',reopened.payment('t1','late-event','late-payment',winner['id'],1000,'USD',20000) == late)
    fault = h.store(Booking,'refund-fault')
    fault.seed('t1','show',{'A':1000})
    held = fault.reserve('t1','alice','op','show',['A'],0)
    fault.db.execute("CREATE TRIGGER fail_refund BEFORE INSERT ON refunds BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('payments','compensation outcome and event commit together',lambda:fault.payment('t1','e','p',held['id'],1000,'USD',5000),
        lambda:fault.db.execute('SELECT count(*) FROM payments').fetchone()[0] == 0 and fault.db.execute('SELECT count(*) FROM events').fetchone()[0] == 0)
    fault.db.execute('DROP TRIGGER fail_refund')
    h.check('payments','retry after compensation rollback succeeds',fault.payment('t1','e','p',held['id'],1000,'USD',5000) == 'refund_required')
    h.observations['late_payment'] = {'last_seat_contenders':2,'admitted_holds':1,'rejected_status':409,
        'old_payment_outcome':late,'reallocated_seat_stolen':False,'one_refund_for_duplicate_payment':True,
        'new_owner_outcome':'confirmed','amount_mismatch_outcome':'review_required',
        'refund_executed_at_provider':False,'compensation_transaction_rollback_tested':True}

    web = h.store(Booking,'http')
    web.seed('t1','show',{'A':1200,'B':1200})
    clock = [0]
    port = h.serve(lambda:Booking(h.root/'http.sqlite'),lambda *args:dispatch(*args,now=clock[0]))
    h.check('http','reservation requires identity',h.request(port,'POST','/holds',{'show':'show','seats':['A']},token='')[0]==401)
    h.check('http','missing operation key is rejected',h.request(port,'POST','/holds',{'show':'show','seats':['A']})[0]==400)
    request = {'show':'show','seats':['A']}
    response = h.request(port,'POST','/holds',request,headers={'Idempotency-Key':'web'})
    hold = response[2]
    h.check('http','real reservation returns authoritative price',response[0]==201 and hold['amount']==1200)
    h.check('http','reservation response is no-store',response[1]['Cache-Control']=='no-store')
    h.check('http','client cannot submit a cheaper price',h.request(port,'POST','/holds',{**request,'price':1},headers={'Idempotency-Key':'cheap'})[0]==400)
    h.check('http','other owner status is hidden',h.request(port,'GET','/holds/'+hold['id'],token='lesson-bob')[0]==404)
    payment = {'tenant':'t1','event_id':'http-e','payment_id':'http-p','hold_id':hold['id'],'amount':1200,'currency':'USD'}
    raw = json.dumps(payment).encode()
    signature = hmac.new(LESSON_PROVIDER_SECRET,raw,hashlib.sha256).hexdigest()
    h.check('http','browser claim cannot confirm payment',h.request(port,'POST','/provider/payment-success',raw)[0]==401)
    accepted = h.request(port,'POST','/provider/payment-success',raw,token='',headers={'X-Lesson-Signature':signature})
    h.check('http','signed raw provider observation confirms',accepted[0]==200 and accepted[2]['outcome']=='confirmed')
    h.check('http','tampered bytes fail before processing',h.request(port,'POST','/provider/payment-success',raw+b' ',token='',headers={'X-Lesson-Signature':signature})[0]==401)
    h.check('http','signed replay remains confirmed',h.request(port,'POST','/provider/payment-success',raw,token='',headers={'X-Lesson-Signature':signature})[2]['outcome']=='confirmed')
    h.check('http','API status reports durable confirmation',h.request(port,'GET','/holds/'+hold['id'])[2]['state']=='confirmed')
    h.check('http','confirmed cancel does not silently release',h.request(port,'DELETE','/holds/'+hold['id'])[0]==409)
    h.observations['http_contract'] = {'reserve_status':201,'server_amount_minor_units':1200,
        'unsigned_payment_status':401,'signed_payment_outcome':'confirmed','tampered_bytes_status':401,
        'foreign_owner_status':404,'confirmed_cancel_status':409,'cache_control':'no-store'}
    h.observations['estimates'] = estimates()
    h.check('estimates','planning request-rate units',estimates()['average_reservation_attempts_per_second']==166.667)
    h.check('estimates','logical storage arithmetic',estimates()['one_million_retained_holds_MB']==512)
    h.check('estimates','not a throughput benchmark',not estimates()['measured_capacity'])
h.report('Local SQLite assigned-seat authority and signed loopback callback only. No real payment/refund, provider SDK, distributed clock/lock, PostgreSQL execution, production auth/TLS or load benchmark. Refund rows are durable pending intents, not executed refunds.')
